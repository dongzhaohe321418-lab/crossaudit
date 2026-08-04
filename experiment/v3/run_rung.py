#!/usr/bin/env python3
"""Run one rung of the isolation ladder over the corpus.

The rungs differ in exactly one thing each, which is the point of a ladder:

  L3   fresh context, no Constitution          model prior alone
  L4   fresh context, with the Constitution    decidable rules added
  L4b  same vendor, a different model          model separation added
  L5   a different vendor                      vendor separation added

L1 and L2 need the generating session and its transcript, so they are driven
separately; the corpus reserves transcript.md for them.

Discipline carried from the v1 runner: temperature 0, one increment per call
with no shared state between calls, provenance digests for every input, and
fail-fast rather than a silent skip.  Outputs are one JSON per increment plus a
manifest, so a crashed run resumes without recomputing what it already has.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time, urllib.request
from pathlib import Path

SYSTEM_BARE = """You are auditing one increment of computational-chemistry work.
Report defects you can substantiate from the material given. Reply with JSON only:
{"findings":[{"location":"<file and field>","description":"<what is wrong>"}]}
An increment with nothing wrong yields an empty findings list."""

SYSTEM_RULES = """You are the Auditor in a supervision protocol. Apply the rulebook
below to one increment and report only what the rulebook makes decidable.
Every finding must cite the rule it applies. Reply with JSON only:
{"sections_applied":["<rule ids you checked>"],
 "findings":[{"rule":"<rule id>","location":"<file and field>","description":"<what is wrong>"}]}
An increment that satisfies the rules yields an empty findings list. Do not invent
rule identifiers: a finding citing a rule that is not in the rulebook is worse than
no finding at all."""

def sha(b: bytes) -> str: return hashlib.sha256(b).hexdigest()

def call_anthropic(model, system, user, key):
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({"model": model, "max_tokens": 2000, "temperature": 0,
                         "system": system, "messages": [{"role": "user", "content": user}]}).encode(),
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = json.loads(r.read())
    return "".join(c.get("text", "") for c in body.get("content", [])), body.get("id", "")

def call_openai(model, system, user, key):
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({"model": model, "temperature": 0,
                         "messages": [{"role": "system", "content": system},
                                      {"role": "user", "content": user}]}).encode(),
        headers={"content-type": "application/json", "authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=180) as r:
        body = json.loads(r.read())
    return body["choices"][0]["message"]["content"], body.get("id", "")

def parse(reply: str):
    t = reply.strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        t = t[4:] if t.lower().startswith("json") else t
    try:
        return json.loads(t), None
    except Exception as e:
        i, j = t.find("{"), t.rfind("}")
        if i >= 0 and j > i:
            try: return json.loads(t[i:j+1]), "recovered from surrounding prose"
            except Exception: pass
        return None, f"unparseable reply: {e}"

def main():
    ap = argparse.ArgumentParser()
    for f in ("rung", "vendor", "model", "constitution", "corpus", "out"):
        ap.add_argument("--" + f, required=True)
    a = ap.parse_args()

    key = os.environ.get("ANTHROPIC_API_KEY" if a.vendor == "anthropic" else "OPENAI_API_KEY", "")
    if not key:
        sys.exit(f"no credential in the environment for vendor {a.vendor}")

    corpus = Path(a.corpus)
    incs = sorted(corpus.glob("INC-*"))
    if not incs: sys.exit(f"no increments under {corpus}")

    rules, rules_sha = "", None
    if a.constitution != "none":
        rp = Path(__file__).resolve().parents[2] / "templates" / "AUDIT_RULES.md"
        rules = rp.read_text(); rules_sha = sha(rules.encode())
    system = SYSTEM_BARE if a.constitution == "none" else SYSTEM_RULES + "\n\n=== RULEBOOK ===\n" + rules

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    done = {p.stem for p in out.glob("INC-*.json")}
    call = call_anthropic if a.vendor == "anthropic" else call_openai
    manifest = {"rung": a.rung, "vendor": a.vendor, "model": a.model,
                "constitution": a.constitution, "constitution_sha256": rules_sha,
                "system_prompt_sha256": sha(system.encode()),
                "corpus": str(corpus), "increments": len(incs), "results": {}}

    for d in incs:
        if d.name in done:
            manifest["results"][d.name] = "already present"; continue
        # Walk the whole increment, not just its top level. An increment that
        # declares geometries/, scripts/ and envs/ and then hands the auditor
        # only the files beside metadata.yml is asking to be told those inputs
        # are missing, and the auditor would be right.
        payload = {str(f.relative_to(d)): f.read_text(errors="replace")
                   for f in sorted(d.rglob("*"))
                   if f.is_file() and f.name != "transcript.md"}
        user = "\n\n".join(f"=== {k} ===\n{v}" for k, v in payload.items())
        t0 = time.time()
        try:
            reply, req_id = call(a.model, system, user, key)
        except Exception as e:
            sys.exit(f"{d.name}: call failed, stopping rather than skipping: {e}")
        parsed, note = parse(reply)
        rec = {"increment": d.name, "rung": a.rung, "vendor": a.vendor, "model": a.model,
               "request_id": req_id, "seconds": round(time.time() - t0, 2),
               "input_sha256": {k: sha(v.encode()) for k, v in payload.items()},
               "reply_sha256": sha(reply.encode()), "raw_reply": reply,
               "parsed": parsed, "parse_note": note}
        (out / f"{d.name}.json").write_text(json.dumps(rec, indent=1) + "\n")
        manifest["results"][d.name] = "ok" if parsed is not None else "unparseable"
        print(f"{d.name}: {len((parsed or {}).get('findings', []))} findings" if parsed
              else f"{d.name}: unparseable")

    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n")
    bad = [k for k, v in manifest["results"].items() if v == "unparseable"]
    print(json.dumps({"rung": a.rung, "increments": len(incs), "unparseable": len(bad)}, indent=1))

if __name__ == "__main__":
    main()
