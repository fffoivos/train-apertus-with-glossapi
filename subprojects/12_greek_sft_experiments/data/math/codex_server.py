#!/usr/bin/env python3
"""Persistent Codex worker: ONE `codex app-server` process per worker, reused across calls (a fresh ephemeral thread per call), instead of one
`codex exec` process per call. JSON-RPC over stdio, newline-delimited (verified 2026-09-11 against codex-cli 0.144.1 / runtime 0.153).
Usage:
    srv = CodexServer(); srv.start()
    obj = srv.call(prompt, schema_dict, model='gpt-5.6-sol', effort='medium', timeout=900)   # dict parsed from the schema-constrained answer
    srv.close()
Concurrent turns on separate threads of one server are supported by the protocol; `call` is thread-safe (writes locked, responses routed by id,
notifications routed by threadId)."""
import json, os, subprocess, threading, queue, time, tempfile, itertools

FLAGS = ['-c', 'features.remote_plugin=false', '-c', 'features.apps=false', '-c', 'features.code_mode_host=false', '-c', 'project_doc_max_bytes=0', '-c', 'notify=[]']


class CodexServer:
    def __init__(self, cwd=None, extra_flags=()):
        self.cwd = cwd or tempfile.mkdtemp(prefix='codex_srv_'); self.extra = list(extra_flags)
        self.p = None; self.ids = itertools.count(1); self.pending = {}; self.threads = {}; self.wlock = threading.Lock(); self.plock = threading.Lock()
        self.seen_methods = {}; self.usage = []

    def start(self):
        self.p = subprocess.Popen(['codex', 'app-server', *FLAGS, *self.extra], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1, cwd=self.cwd)
        threading.Thread(target=self._reader, daemon=True).start()
        r = self._request('initialize', {'clientInfo': {'name': 'sft_worker', 'title': 'SFT worker', 'version': '0.1'}, 'capabilities': {'experimentalApi': True}}, timeout=60)
        return r

    def _reader(self):
        for line in self.p.stdout:
            try: msg = json.loads(line)
            except Exception: continue
            if 'id' in msg and ('result' in msg or 'error' in msg):
                with self.plock: fut = self.pending.pop(msg['id'], None)
                if fut: fut.put(msg)
            elif 'method' in msg:
                m = msg['method']; self.seen_methods[m] = self.seen_methods.get(m, 0) + 1
                tid = (msg.get('params') or {}).get('threadId')
                q = self.threads.get(tid) if tid else None
                if q: q.put(msg)
                # server-initiated requests (approvals) would carry an id + method; none expected with read-only sandbox

    def _request(self, method, params, timeout=900):
        rid = next(self.ids); fut = queue.Queue()
        with self.plock: self.pending[rid] = fut
        with self.wlock: self.p.stdin.write(json.dumps({'method': method, 'id': rid, 'params': params}) + '\n'); self.p.stdin.flush()
        try: msg = fut.get(timeout=timeout)
        except queue.Empty: raise TimeoutError(f'{method} timed out')
        if 'error' in msg: raise RuntimeError(f'{method}: {msg["error"]}')
        return msg['result']

    def call(self, prompt, schema, model='gpt-5.6-sol', effort='medium', timeout=900):
        r = self._request('thread/start', {'model': model, 'ephemeral': True, 'cwd': self.cwd, 'sandbox': 'read-only'}, timeout=120)
        tid = r['thread']['id']; q = queue.Queue(); self.threads[tid] = q
        try:
            self._request('turn/start', {'threadId': tid, 'input': [{'type': 'text', 'text': prompt}], 'model': model, 'effort': effort, 'outputSchema': schema, 'sandboxPolicy': {'type': 'readOnly'}}, timeout=120)
            text, deadline, done = [], time.time() + timeout, None
            while time.time() < deadline:
                try: msg = q.get(timeout=min(30, max(1, deadline - time.time())))
                except queue.Empty: continue
                m, p = msg['method'], msg.get('params') or {}
                if m == 'item/agentMessage/delta': text.append(p.get('delta', ''))
                elif m == 'item/completed' and (p.get('item') or {}).get('type') == 'agentMessage':
                    t = (p['item'].get('text') or p['item'].get('content') or ''); 
                    if isinstance(t, str) and t: text = [t]
                elif m == 'turn/completed':
                    done = p.get('turn') or {}; 
                    if done.get('usage'): self.usage.append(done['usage'])
                    break
                elif m in ('thread/tokenUsage/updated', 'thread/usage/updated'): self.usage.append(p)
            if done is None: raise TimeoutError('turn did not complete')
            if done.get('status') == 'failed': raise RuntimeError(f'turn failed: {done.get("error")}')
            raw = ''.join(text).strip()
            return json.loads(raw[raw.index('{'):raw.rindex('}') + 1])
        finally:
            self.threads.pop(tid, None)
            try: self._request('thread/close', {'threadId': tid}, timeout=10)
            except Exception: pass

    def close(self):
        try: self.p.stdin.close(); self.p.terminate()
        except Exception: pass
