#!/usr/bin/env python3
"""generator 0.2 with ONE thing changed: what the person, the situation and the topic are FOR.

generate.py is not edited. This imports it, replaces two sentences of INSTANCE_PROMPT and one of REVIEW_PROMPT, and calls
its main() -- same flags, same checks, same review, same repairs.

Why (measured on 408 real seeded prompts, 21 Sept): two seeds sharing a SITUATION come out 3.3x (el) / 4.3x (en) more
alike than average; sharing a TOPIC 1.3x / 1.1x; sharing a PERSON 1.0x. The stock prompt says why: the topic may be dropped
("drop the topic if it does not fit; never force it"), the situations are written as complete scenarios so they already
own the subject and the topic has nowhere to go, and all three are demoted to "ingredients for realism".

Here each element gets a distinct job:
  topic      what the request is ABOUT. Mandatory.
  situation  why the person asks NOW: the pressure or constraint, applied to the topic. Never the subject.
  person     what changes a GOOD ANSWER: what they know, cannot do, have to hand. Not a biography to recite.
"""
import pathlib, sys
GEN = pathlib.Path(__file__).resolve().parents[2] / "generator_v02"
sys.path.insert(0, str(GEN)); sys.path.insert(0, str(GEN.parents[1] / "math"))
import generate as g

OLD_1 = "touching that topic where it fits naturally (drop the topic if it does not fit; never force it)."
NEW_1 = ("The three ingredients have DIFFERENT jobs. TOPIC: what the request is about -- the subject matter of the task must be that topic; "
         "never drop it and never swap it. SITUATION: why this person asks right now -- take from it only the circumstance (the deadline, "
         "the audience, the failed earlier attempt, the missing information, the interruption, the stakes) and apply that circumstance to "
         "the topic; if the situation text names a subject of its own, discard that subject and keep the circumstance. PERSON: their work, "
         "experience and means must change what a good answer looks like -- put into the instance at least one given that follows from "
         "who they are (what they already know or have tried, what they cannot do, what they have to hand, who the result is for), "
         "stated the way that person would state it, not as a biography.")
OLD_2 = "The person, situation and topic are ingredients for realism, not a scenario template: most real requests do not involve juggling a work schedule; vary the kind of need widely."
NEW_2 = ("Most real requests do not involve juggling a work schedule; vary the kind of need widely. Do not let the situation decide the "
         "subject: two instances built from the same situation and different topics must be about visibly different things.")
assert OLD_1 in g.INSTANCE_PROMPT and OLD_2 in g.INSTANCE_PROMPT, "generate.py's INSTANCE_PROMPT changed; this variant must be re-derived"
g.INSTANCE_PROMPT = g.INSTANCE_PROMPT.replace(OLD_1, NEW_1).replace(OLD_2, NEW_2)
# CP2 M5: the reviewer failed 6 of 13 renderings for omitting the persona blurb, and the repair injected "I am 29, based in...".
OLD_3 = "do not fail for style you merely dislike."
assert OLD_3 in g.REVIEW_PROMPT
g.REVIEW_PROMPT = g.REVIEW_PROMPT.replace(OLD_3, OLD_3 + " Never fail a message for leaving out the person's age, job title, city or life story: "
                                          "those shape the request, they are not givens the person must recite.")
if __name__ == "__main__":
    import hashlib
    print("VARIANT generate_roles.py sha16=%s instance_prompt_sha16=%s review_prompt_sha16=%s" % (
        hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()[:16], hashlib.sha256(g.INSTANCE_PROMPT.encode()).hexdigest()[:16],
        hashlib.sha256(g.REVIEW_PROMPT.encode()).hexdigest()[:16]), flush=True)
    g.main()
