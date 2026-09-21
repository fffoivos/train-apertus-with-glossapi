"""PromptBank: every prompt is tied to exactly one source, and the database refuses anything else.

The registry this replaces (data/rlhf/registry/registry.sqlite) was clean when audited on 2026-09-21 --
0 orphans, 0 exact duplicates -- but it was clean by DISCIPLINE. Its schema had no foreign keys, no
UNIQUE on content and no NOT NULL on the source link, and it was filled by a post-hoc `import` that
scraped generator output. The forum path had no memory at all: forum_select.py sampled JSONL with a
random seed, so nothing stopped a second draw from returning a URL already used. And the target
distribution was only ever REPORTED, which is how astrovox reached 9.4% of forum prompts against a 3%
cap without anything objecting.

Here those three properties are structural:

  provenance    prompts.source_id is NOT NULL (schema-level: no connection can insert a prompt with no
                source) and a FOREIGN KEY. SQLite enforces foreign keys PER CONNECTION, so the FK is
                unbreakable through PromptBank and merely DETECTABLE through a bare sqlite3 connection:
                audit() counts such orphans. (CP1 review, M1: the first wording overclaimed this.)
  no duplicates sources are UNIQUE on (kind, natural_key) -- one row per forum URL, one per canonical
                seed. prompts are UNIQUE on content_sha. A partial unique index allows at most ONE
                active prompt per source, so a retry must supersede, never sit alongside. Near-
                duplicates are refused by exact Jaccard over word 5-grams, found through an index.
  distribution  a plan turns target shares into integer quotas (largest remainder, so they sum to n
                exactly). claim() hands out only sources whose cell still has room; submit(), supersede()
                and set_status() re-check inside the same transaction. A quota cannot be OVERSHOT by any
                caller in any order (verified under 8 processes). What is NOT guaranteed is COMPLETION:
                claim() is greedy, so it can spend the one source a later joint cell needed.
                feasibility() checks joint attainability by max-flow, so that dead end is at least visible.

Standard library only. One writer at a time per transaction (BEGIN IMMEDIATE); safe across processes.
"""
import collections, contextlib, hashlib, json, re, sqlite3, time, unicodedata

KINDS = ("seed", "forum", "template", "dialogue")
SOURCE_STATES = ("available", "claimed", "consumed", "rejected", "retired")
PROMPT_STATES = ("active", "held", "superseded", "rejected", "archived")
LIVE = ("active", "held")                 # the states that OCCUPY A SOURCE and block duplicates.
# Only 'active' fills a quota. A held prompt failed review and is waiting for a retry: it must keep its source
# (so nobody re-draws it blind) but it must not count towards the distribution, or a plan could read "full"
# while a fifth of it is unusable -- generator 0.2 holds about 18% of what it renders.
NEAR_DUPLICATE_JACCARD = 0.5
DIMENSIONS = ("purpose", "language", "kind", "forum")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources(
  source_id   TEXT PRIMARY KEY,
  kind        TEXT NOT NULL CHECK(kind IN ('seed','forum','template','dialogue')),
  natural_key TEXT NOT NULL,              -- forum: the URL. seed/template/dialogue: canonical JSON of the seed.
  forum       TEXT,
  purpose     TEXT NOT NULL,
  language    TEXT NOT NULL,
  payload     TEXT NOT NULL,              -- the source itself, verbatim, so a prompt can always be re-derived
  state       TEXT NOT NULL DEFAULT 'available'
              CHECK(state IN ('available','claimed','consumed','rejected','retired')),
  state_reason TEXT,
  claimed_plan TEXT REFERENCES plans(plan_id),
  claimed_by  TEXT,
  claimed_at  REAL,
  origin      TEXT NOT NULL,              -- which generator / gate version produced this source
  created     REAL NOT NULL,
  UNIQUE(kind, natural_key),
  CHECK((kind = 'forum') = (forum IS NOT NULL)),
  CHECK((state = 'claimed') = (claimed_plan IS NOT NULL)));
CREATE INDEX IF NOT EXISTS sources_pick ON sources(kind, state, purpose, language, forum);

CREATE TABLE IF NOT EXISTS plans(
  plan_id TEXT PRIMARY KEY, n INTEGER NOT NULL CHECK(n > 0), spec TEXT NOT NULL, created REAL NOT NULL);

CREATE TABLE IF NOT EXISTS quotas(
  plan_id   TEXT NOT NULL REFERENCES plans(plan_id),
  dimension TEXT NOT NULL CHECK(dimension IN ('purpose','language','kind','forum')),
  key       TEXT NOT NULL,
  mode      TEXT NOT NULL CHECK(mode IN ('share','cap')),   -- share: a goal AND a ceiling, and the dimension
  target    INTEGER,                                        --   is CLOSED (an unlisted key is refused).
  maximum   INTEGER NOT NULL CHECK(maximum >= 0),           -- cap: a ceiling only; unlisted keys are free.
  PRIMARY KEY(plan_id, dimension, key),
  CHECK((mode = 'share') = (target IS NOT NULL)));

CREATE TABLE IF NOT EXISTS prompts(
  prompt_id   TEXT PRIMARY KEY,
  source_id   TEXT NOT NULL REFERENCES sources(source_id),
  plan_id     TEXT REFERENCES plans(plan_id),               -- NULL only for prompts that predate plans
  content_sha TEXT NOT NULL UNIQUE,
  messages    TEXT NOT NULL,
  n_shingles  INTEGER NOT NULL,
  kind        TEXT NOT NULL, forum TEXT, purpose TEXT NOT NULL, language TEXT NOT NULL,
  status      TEXT NOT NULL CHECK(status IN ('active','held','superseded','rejected','archived')),
  status_reason TEXT,
  supersedes  TEXT REFERENCES prompts(prompt_id),
  generator   TEXT NOT NULL, run TEXT NOT NULL, labels TEXT NOT NULL, created REAL NOT NULL);
CREATE UNIQUE INDEX IF NOT EXISTS one_live_prompt_per_source ON prompts(source_id) WHERE status IN ('active','held');
CREATE INDEX IF NOT EXISTS prompts_plan ON prompts(plan_id, status);

CREATE TABLE IF NOT EXISTS shingles(
  prompt_id TEXT NOT NULL REFERENCES prompts(prompt_id), h INTEGER NOT NULL, PRIMARY KEY(prompt_id, h)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS shingles_h ON shingles(h);

CREATE TABLE IF NOT EXISTS aliases(
  alias TEXT PRIMARY KEY, prompt_id TEXT NOT NULL REFERENCES prompts(prompt_id), note TEXT);
"""


class BankError(Exception): pass
class SourceError(BankError): pass
class QuotaError(BankError): pass
class DuplicateError(BankError):
    def __init__(self, msg, existing, similarity=1.0):
        super().__init__(msg); self.existing, self.similarity = existing, similarity
class NearDuplicateError(DuplicateError): pass


def _norm(s): return re.sub(r"\s+", " ", unicodedata.normalize("NFC", s or "")).strip()

def content_sha(messages):
    """Identity of a prompt's text. Same canonical form as the legacy registry, so ids carry over."""
    return hashlib.sha256(json.dumps([[m["role"], _norm(m["content"])] for m in messages],
                                     ensure_ascii=False).encode()).hexdigest()

def _fold(s):
    """Lower-case and strip combining marks, so 'Πώς υπολογίζεται' and 'Πως υπολογιζεται' are the same words."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))

def shingle_set(messages, k=5, short=8):
    """Word k-grams of the USER turns -- case-, accent- and punctuation-insensitive -- as 63-bit ints.
    Under `short` words a word k-gram is all-or-nothing (a 4-word prompt is ONE gram), so short prompts use
    character 4-grams instead. A prompt with no user text gets a gram of its own content hash: no shared bucket."""
    text = _fold(" ".join(_norm(m["content"]) for m in messages if m["role"] == "user"))
    words = re.sub(r"[^\w\s]", " ", text).split()
    if not words: grams = ["\x00empty:" + content_sha(messages)]
    elif len(words) < short:
        t = " ".join(words); grams = ["c:" + t[i:i + 4] for i in range(max(1, len(t) - 3))]
    else: grams = [" ".join(words[i:i + k]) for i in range(len(words) - k + 1)]
    return {int.from_bytes(hashlib.blake2b(g.encode(), digest_size=8).digest(), "big") >> 1 for g in grams}

def source_id_for(kind, natural_key):
    return "%s:%s" % (kind, hashlib.sha256(("%s\x00%s" % (kind, natural_key)).encode()).hexdigest()[:16])

def apportion(n, shares):
    """Largest-remainder rounding: integer quotas that sum to EXACTLY n. Ties break by key, so it is stable."""
    if any((not isinstance(v, (int, float))) or v != v or v in (float("inf"), float("-inf")) or v < 0 for v in shares.values()):
        raise BankError("weights must be finite and >= 0: %r" % (shares,))
    total = float(sum(shares.values()))
    if total <= 0: raise BankError("shares sum to zero")
    exact = {k: n * v / total for k, v in shares.items()}
    out = {k: int(x) for k, x in exact.items()}
    for k in sorted(shares, key=lambda k: (-(exact[k] - out[k]), k))[: n - sum(out.values())]: out[k] += 1
    return out


def _max_flow(need_p, need_l, cells):
    """Places fillable when purpose p still needs need_p[p], language l needs need_l[l], and cells[(p,l)] sources exist.
    Edmonds-Karp on  S -> purpose -> language -> T ; tiny graphs, stdlib only."""
    S, T = ("S",), ("T",); cap = collections.defaultdict(lambda: collections.defaultdict(int))
    for p, n in need_p.items(): cap[S][("p", p)] += n
    for l, n in need_l.items(): cap[("l", l)][T] += n
    for (p, l), n in cells.items():
        if p in need_p and l in need_l: cap[("p", p)][("l", l)] += n
    flow = 0
    while True:
        prev, queue = {S: None}, collections.deque([S])
        while queue and T not in prev:
            u = queue.popleft()
            for v, c in list(cap[u].items()):
                if c > 0 and v not in prev: prev[v] = u; queue.append(v)
        if T not in prev: return flow
        path, v = [], T
        while prev[v] is not None: path.append((prev[v], v)); v = prev[v]
        push = min(cap[u][v] for u, v in path)
        for u, v in path: cap[u][v] -= push; cap[v][u] += push
        flow += push


class PromptBank:
    def __init__(self, path):
        self.path = str(path)
        self.db = sqlite3.connect(self.path, timeout=60, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        if self.db.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise BankError("this SQLite build cannot enforce foreign keys; the bank's guarantees would be fiction")
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.executescript(SCHEMA)

    @contextlib.contextmanager
    def _tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
            self.db.execute("COMMIT")
        except BaseException:
            self.db.execute("ROLLBACK"); raise

    # ------------------------------------------------------------------ sources
    def add_source(self, kind, natural_key, *, purpose, language, payload, origin, forum=None, state="available", reason=None):
        """Idempotent on (kind, natural_key): adding a known source returns its id and changes nothing."""
        if kind not in KINDS: raise SourceError("unknown kind %r" % kind)
        sid = source_id_for(kind, natural_key)
        with self._tx() as db:
            # NOT "INSERT OR IGNORE": in SQLite that also swallows CHECK and NOT NULL violations, so a malformed
            # source would vanish silently while this returned an id for a row that does not exist.
            if db.execute("SELECT 1 FROM sources WHERE source_id=?", (sid,)).fetchone(): return sid
            db.execute("INSERT INTO sources(source_id,kind,natural_key,forum,purpose,language,payload,state,state_reason,origin,created)"
                       " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                       (sid, kind, natural_key, forum, purpose, language, json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        state, reason, origin, time.time()))
        return sid

    def release(self, source_id):
        """Give a claimed source back unused."""
        with self._tx() as db:
            n = db.execute("UPDATE sources SET state='available', claimed_plan=NULL, claimed_by=NULL, claimed_at=NULL WHERE source_id=? AND state='claimed'", (source_id,)).rowcount
        if not n: raise SourceError("%s is not claimed" % source_id)

    def reject_source(self, source_id, reason):
        """The source turned out unusable. It is never offered again."""
        with self._tx() as db:
            if db.execute("SELECT 1 FROM prompts WHERE source_id=? AND status IN ('active','held')", (source_id,)).fetchone():
                raise SourceError("%s has a live prompt; retire that first" % source_id)
            db.execute("UPDATE sources SET state='rejected', state_reason=?, claimed_plan=NULL, claimed_by=NULL, claimed_at=NULL WHERE source_id=?", (reason, source_id))

    # ------------------------------------------------------------------ plans
    def plan(self, plan_id, n, *, shares, caps=None):
        """shares = {dimension: {key: weight}} -> closed quotas summing to n per dimension.
        caps   = {dimension: {key: max_count}}  -> ceilings on an otherwise open dimension."""
        caps = caps or {}
        for d in list(shares) + list(caps):
            if d not in DIMENSIONS: raise BankError("unknown dimension %r" % d)
        if set(shares) & set(caps): raise BankError("a dimension is either shared or capped, not both: %s" % (set(shares) & set(caps)))
        with self._tx() as db:
            db.execute("INSERT INTO plans VALUES (?,?,?,?)", (plan_id, n, json.dumps({"shares": shares, "caps": caps}, sort_keys=True), time.time()))
            for d, sh in shares.items():
                for k, q in apportion(n, sh).items():
                    db.execute("INSERT INTO quotas VALUES (?,?,?,'share',?,?)", (plan_id, d, k, q, q))
            for d, cp in caps.items():
                for k, m in cp.items():
                    db.execute("INSERT INTO quotas VALUES (?,?,?,'cap',NULL,?)", (plan_id, d, k, int(m)))
        return plan_id

    def _usage(self, db, plan_id):
        """{(dimension, key): (filled, claimed)} for one plan. ACTIVE prompts fill; outstanding claims reserve."""
        use = {}
        for d in DIMENSIONS:
            for k, c in db.execute("SELECT %s, COUNT(*) FROM prompts WHERE plan_id=? AND status='active' GROUP BY 1" % d, (plan_id,)):
                use[(d, k)] = [c, 0]
            for k, c in db.execute("SELECT %s, COUNT(*) FROM sources WHERE claimed_plan=? AND state='claimed' GROUP BY 1" % d, (plan_id,)):
                use.setdefault((d, k), [0, 0])[1] = c
        return use

    def _room(self, db, plan_id, cell, counting_claims, usage=None):
        """None if a prompt in `cell` fits the plan, else the reason it does not."""
        quotas = {(r["dimension"], r["key"]): r for r in db.execute("SELECT * FROM quotas WHERE plan_id=?", (plan_id,))}
        closed = {d for (d, _), r in quotas.items() if r["mode"] == "share"}
        usage = self._usage(db, plan_id) if usage is None else usage
        for d in DIMENSIONS:
            k = cell.get(d); q = quotas.get((d, k))
            if q is None:
                if d in closed: return "%s=%r is not in plan %s" % (d, k, plan_id)
                continue
            filled, claimed = usage.get((d, k), (0, 0))
            if filled + (claimed if counting_claims else 0) >= q["maximum"]:
                return "%s=%r is full in plan %s (%d of %d)" % (d, k, plan_id, filled, q["maximum"])
        return None

    def claim(self, plan_id, kind, *, worker, purpose=None, language=None, forum=None, peek=False):
        """Reserve ONE unused source whose cell still has room in the plan, or return None if there is none.

        When no forum is named, the forum with the fewest prompts+claims so far in this plan goes first,
        so forums fill evenly instead of in file order. Within a forum the order is a hash of
        (plan, source): arbitrary, but identical on every machine and every re-run."""
        with self._tx() as db:
            if not db.execute("SELECT 1 FROM plans WHERE plan_id=?", (plan_id,)).fetchone(): raise BankError("no plan %r" % plan_id)
            sql, args = "SELECT source_id, kind, forum, purpose, language FROM sources WHERE state='available' AND kind=?", [kind]
            for col, v in (("purpose", purpose), ("language", language), ("forum", forum)):
                if v is not None: sql += " AND %s=?" % col; args.append(v)
            usage = self._usage(db, plan_id)
            load = lambda f: sum(usage.get(("forum", f), (0, 0)))
            order = lambda r: (load(r["forum"]) if r["forum"] else 0,
                               hashlib.sha256(("%s\x00%s" % (plan_id, r["source_id"])).encode()).hexdigest())
            for r in sorted(db.execute(sql, args).fetchall(), key=order):
                if self._room(db, plan_id, dict(r), counting_claims=True, usage=usage) is None:
                    if peek: return self.source(r["source_id"])      # "is anything claimable?" without touching state
                    db.execute("UPDATE sources SET state='claimed', claimed_plan=?, claimed_by=?, claimed_at=? WHERE source_id=?", (plan_id, worker, time.time(), r["source_id"]))
                    return self.source(r["source_id"])
        return None

    # ------------------------------------------------------------------ prompts
    def _near(self, db, sh, exclude_source):
        shared = {}
        sh = list(sh)
        for i in range(0, len(sh), 400):
            part = sh[i:i + 400]
            for pid, c in db.execute("SELECT s.prompt_id, COUNT(*) FROM shingles s JOIN prompts p USING(prompt_id) "
                                     "WHERE p.status IN ('active','held') AND p.source_id != ? AND s.h IN (%s) GROUP BY 1"
                                     % ",".join("?" * len(part)), [exclude_source] + part):
                shared[pid] = shared.get(pid, 0) + c
        best = (0.0, None)
        for pid, c in shared.items():
            n = db.execute("SELECT n_shingles FROM prompts WHERE prompt_id=?", (pid,)).fetchone()[0]
            best = max(best, (c / float(len(sh) + n - c), pid))
        return best

    def _insert(self, db, source_id, messages, plan_id, run, generator, labels, purpose, language, status, reason, supersedes, allow_near, legacy=False):
        src = db.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        if src is None: raise SourceError("no such source %r: a prompt must come from a registered source" % source_id)
        if src["state"] in ("rejected", "retired") and status in LIVE:
            raise SourceError("%s is %s (%s)" % (source_id, src["state"], src["state_reason"]))
        if src["state"] == "consumed" and status in LIVE and not (legacy or supersedes):
            # its live prompt may since have been archived, but the source was USED. A fresh live prompt on it is a
            # reuse: go through supersede(). (CP1 M6. `legacy` exists for migrate.py, which replays history in order.)
            raise SourceError("%s was already consumed; a new live prompt on it must go through supersede()" % source_id)
        if src["state"] == "claimed" and plan_id != src["claimed_plan"]:
            raise SourceError("%s is claimed for plan %s, not %s" % (source_id, src["claimed_plan"], plan_id))
        sha = content_sha(messages)
        hit = db.execute("SELECT prompt_id FROM prompts WHERE content_sha=?", (sha,)).fetchone()
        if hit: raise DuplicateError("identical text already registered as %s" % hit[0], hit[0])
        sh = shingle_set(messages)
        if status in LIVE:
            if db.execute("SELECT 1 FROM prompts WHERE source_id=? AND status IN ('active','held')", (source_id,)).fetchone():
                raise SourceError("%s already has a live prompt; use supersede() for a retry" % source_id)
            if not allow_near:
                j, other = self._near(db, sh, source_id)
                if j >= NEAR_DUPLICATE_JACCARD:
                    raise NearDuplicateError("%.2f word-5-gram overlap with %s" % (j, other), other, j)
        cell = {"purpose": purpose or src["purpose"], "language": language or src["language"], "kind": src["kind"], "forum": src["forum"]}
        if plan_id is not None and status == "active":
            why = self._room(db, plan_id, cell, counting_claims=False)
            if why: raise QuotaError(why)
        pid = "p:" + sha[:16]
        db.execute("INSERT INTO prompts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (pid, source_id, plan_id, sha, json.dumps(messages, ensure_ascii=False), len(sh), cell["kind"], cell["forum"],
                    cell["purpose"], cell["language"], status, reason, supersedes, generator, run,
                    json.dumps(labels or {}, ensure_ascii=False, sort_keys=True), time.time()))
        db.executemany("INSERT INTO shingles VALUES (?,?)", [(pid, h) for h in sh])
        # recording HISTORY neither revives a dead source nor burns a fresh one (CP1 M9): only a live prompt, or a
        # legacy replay, consumes.
        if src["state"] not in ("rejected", "retired") and (status in LIVE or legacy):
            db.execute("UPDATE sources SET state='consumed', claimed_plan=NULL, claimed_by=NULL, claimed_at=NULL WHERE source_id=?", (source_id,))
        return pid

    def submit(self, source_id, messages, *, run, generator, plan_id=None, labels=None, purpose=None, language=None,
               status="active", reason=None, allow_near_duplicate=False, legacy=False):
        """Register the prompt made from `source_id`. Raises rather than degrade:
        SourceError (unknown / spent / rejected source), DuplicateError, NearDuplicateError, QuotaError."""
        if status not in PROMPT_STATES: raise BankError("unknown status %r" % status)
        with self._tx() as db:
            return self._insert(db, source_id, messages, plan_id, run, generator, labels, purpose, language, status, reason, None, allow_near_duplicate, legacy)

    def supersede(self, prompt_id, messages, *, run, generator, labels=None, reason="retry", allow_near_duplicate=False):
        """A retry: the old prompt becomes 'superseded' and the new one takes its source, plan and cell, atomically."""
        with self._tx() as db:
            old = db.execute("SELECT * FROM prompts WHERE prompt_id=?", (prompt_id,)).fetchone()
            if old is None: raise BankError("no such prompt %r" % prompt_id)
            if old["status"] not in LIVE: raise BankError("%s is %s; only a live prompt can be superseded" % (prompt_id, old["status"]))
            db.execute("UPDATE prompts SET status='superseded', status_reason=? WHERE prompt_id=?", (reason, prompt_id))
            return self._insert(db, old["source_id"], messages, old["plan_id"], run, generator, labels, old["purpose"], old["language"],
                                "active", None, prompt_id, allow_near_duplicate)

    def set_status(self, prompt_id, status, reason):
        """Retire, hold or approve a prompt, under the same rules as submit().

        CP1 H1: this used to be a bare UPDATE, so held -> active (a reviewer approving a held prompt) walked straight
        past the quota, and superseded -> active resurrected a prompt beside its own retry. Now:
          * a prompt that is superseded / rejected / archived stays dead. A retry is supersede(), not a status flip.
          * becoming 'active' re-checks the plan's room inside the transaction, exactly as submit() does.
        A retired prompt's source stays consumed: rejecting a prompt does not make its source fresh again."""
        if status not in PROMPT_STATES: raise BankError("unknown status %r" % status)
        with self._tx() as db:
            p = db.execute("SELECT * FROM prompts WHERE prompt_id=?", (prompt_id,)).fetchone()
            if p is None: raise BankError("no such prompt %r" % prompt_id)
            if p["status"] == status: return
            if p["status"] not in LIVE:
                raise BankError("%s is %s and stays that way; a new attempt on its source goes through supersede()" % (prompt_id, p["status"]))
            if status == "active" and p["plan_id"] is not None:
                why = self._room(db, p["plan_id"], {d: p[d] for d in DIMENSIONS}, counting_claims=False)
                if why: raise QuotaError(why)
            db.execute("UPDATE prompts SET status=?, status_reason=? WHERE prompt_id=?", (status, reason, prompt_id))

    def release_stale(self, older_than_seconds=3600, plan_id=None):
        """Give back claims nobody is going to honour (a worker died mid-call). Returns the source ids released.
        CP1 H2: a stuck claim is worse than a lost source -- it reserves a place in the plan for ever."""
        with self._tx() as db:
            sql, args = "SELECT source_id FROM sources WHERE state='claimed' AND claimed_at < ?", [time.time() - older_than_seconds]
            if plan_id: sql += " AND claimed_plan=?"; args.append(plan_id)
            ids = [r[0] for r in db.execute(sql, args)]
            db.executemany("UPDATE sources SET state='available', claimed_plan=NULL, claimed_by=NULL, claimed_at=NULL WHERE source_id=?", [(i,) for i in ids])
        return ids

    def alias(self, alias, prompt_id, note=None):
        with self._tx() as db: db.execute("INSERT OR REPLACE INTO aliases VALUES (?,?,?)", (alias, prompt_id, note))

    # ------------------------------------------------------------------ reading
    def source(self, source_id):
        r = self.db.execute("SELECT * FROM sources WHERE source_id=?", (source_id,)).fetchone()
        if r is None: raise SourceError("no such source %r" % source_id)
        d = dict(r); d["payload"] = json.loads(d["payload"]); return d

    def lineage(self, prompt_id):
        """The prompt, the source it came from, and every earlier attempt on that source."""
        hit = self.db.execute("SELECT prompt_id FROM aliases WHERE alias=?", (prompt_id,)).fetchone()
        if hit: prompt_id = hit[0]
        p = self.db.execute("SELECT * FROM prompts WHERE prompt_id=?", (prompt_id,)).fetchone()
        if p is None: raise BankError("no such prompt %r" % prompt_id)
        p = dict(p); p["messages"] = json.loads(p["messages"]); p["labels"] = json.loads(p["labels"])
        hist = [dict(r) for r in self.db.execute("SELECT prompt_id, status, status_reason, run, created FROM prompts WHERE source_id=? ORDER BY created", (p["source_id"],))]
        return {"prompt": p, "source": self.source(p["source_id"]), "attempts_on_this_source": hist,
                "aliases": [r[0] for r in self.db.execute("SELECT alias FROM aliases WHERE prompt_id=?", (prompt_id,))]}

    def coverage(self, plan_id):
        """One row per quota: target, ceiling, filled, claimed, remaining. The plan is met when every share row has remaining 0."""
        use = self._usage(self.db, plan_id); out = []
        for q in self.db.execute("SELECT * FROM quotas WHERE plan_id=? ORDER BY dimension, mode, maximum DESC, key", (plan_id,)):
            f, c = use.get((q["dimension"], q["key"]), (0, 0))
            out.append({"dimension": q["dimension"], "key": q["key"], "mode": q["mode"], "target": q["target"], "maximum": q["maximum"],
                        "filled": f, "claimed": c, "remaining": q["maximum"] - f})
        return out

    def feasibility(self, plan_id):
        """Can the unused supply still meet the plan? Empty means yes.

        Two checks. Per dimension: is there enough Greek, enough maths. Then JOINTLY over purpose x language, by
        max-flow: enough Greek and enough maths is not enough Greek maths, and because claim() is greedy it can
        itself create that dead end by spending the one source a later cell needed (CP1 M2 reproduced it with
        three sources). The joint row reports how many places can no longer be filled by ANY assignment."""
        out, cov = [], self.coverage(plan_id)
        for r in cov:
            if r["mode"] != "share" or r["remaining"] <= 0: continue
            have = self.db.execute("SELECT COUNT(*) FROM sources WHERE state IN ('available','claimed') AND %s=?" % r["dimension"], (r["key"],)).fetchone()[0]
            if have < r["remaining"]:
                out.append({"dimension": r["dimension"], "key": r["key"], "still_needed": r["remaining"], "unused_sources": have, "short_by": r["remaining"] - have})
        need = {d: {r["key"]: r["remaining"] for r in cov if r["dimension"] == d and r["mode"] == "share" and r["remaining"] > 0} for d in ("purpose", "language")}
        if need["purpose"] and need["language"]:
            cells = {(r[0], r[1]): r[2] for r in self.db.execute(
                "SELECT purpose, language, COUNT(*) FROM sources WHERE state IN ('available','claimed') GROUP BY 1,2")}
            want = min(sum(need["purpose"].values()), sum(need["language"].values()))
            got = _max_flow(need["purpose"], need["language"], cells)
            if got < want:
                out.append({"dimension": "purpose x language (joint)", "key": "*", "still_needed": want, "unused_sources": sum(cells.values()),
                            "short_by": want - got, "note": "no assignment of the unused sources can fill these places"})
        return out

    def supply(self, kind=None):
        """Unused sources per cell: what is still available to draw from."""
        sql = "SELECT kind, forum, purpose, language, COUNT(*) n FROM sources WHERE state='available'" + (" AND kind=?" if kind else "") + " GROUP BY 1,2,3,4 ORDER BY 1,2,3,4"
        return [dict(r) for r in self.db.execute(sql, (kind,) if kind else ())]

    def stats(self):
        g = lambda s: {(r[0] if len(r) == 2 else tuple(r[:-1])): r[-1] for r in self.db.execute(s)}
        return {"sources": g("SELECT kind, state, COUNT(*) FROM sources GROUP BY 1,2"),
                "prompts": g("SELECT kind, status, COUNT(*) FROM prompts GROUP BY 1,2")}

    def audit(self):
        """Every entry should be 0 or empty. The first four cannot be non-zero unless the schema was bypassed;
        they are checked anyway because 'cannot happen' is exactly what an audit is for."""
        one = lambda s: self.db.execute(s).fetchone()[0]
        over = []
        for pid, in self.db.execute("SELECT plan_id FROM plans"):
            over += ["%s %s=%s %d>%d" % (pid, r["dimension"], r["key"], r["filled"], r["maximum"]) for r in self.coverage(pid) if r["filled"] > r["maximum"]]
        return {"foreign_key_violations": len(self.db.execute("PRAGMA foreign_key_check").fetchall()),
                "integrity": self.db.execute("PRAGMA integrity_check").fetchone()[0],
                "prompts_without_source": one("SELECT COUNT(*) FROM prompts p WHERE NOT EXISTS(SELECT 1 FROM sources s WHERE s.source_id=p.source_id)"),
                "sources_with_two_live_prompts": one("SELECT COUNT(*) FROM (SELECT source_id FROM prompts WHERE status IN ('active','held') GROUP BY 1 HAVING COUNT(*)>1)"),
                "duplicate_content": one("SELECT COUNT(*) FROM (SELECT content_sha FROM prompts GROUP BY 1 HAVING COUNT(*)>1)"),
                "consumed_sources_with_no_prompt": one("SELECT COUNT(*) FROM sources s WHERE state='consumed' AND NOT EXISTS(SELECT 1 FROM prompts p WHERE p.source_id=s.source_id)"),
                "live_prompts_on_unconsumed_source": one("SELECT COUNT(*) FROM prompts p JOIN sources s USING(source_id) WHERE p.status IN ('active','held') AND s.state!='consumed'"),
                "prompt_cell_disagrees_with_source_kind": one("SELECT COUNT(*) FROM prompts p JOIN sources s USING(source_id) WHERE p.kind!=s.kind OR IFNULL(p.forum,'')!=IFNULL(s.forum,'')"),
                "stale_claims_older_than_an_hour": one("SELECT COUNT(*) FROM sources WHERE state='claimed' AND claimed_at < %f" % (time.time() - 3600)),
                "stale_claims_older_than_a_day": one("SELECT COUNT(*) FROM sources WHERE state='claimed' AND claimed_at < %f" % (time.time() - 86400)),
                "quotas_overshot": over}
