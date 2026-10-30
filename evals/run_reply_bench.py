#!/usr/bin/env python3
"""답변 register 측정. 독자가 채팅 답변에서 보는 것을 셉니다.

reply_scenarios.json의 질문마다 조건별로 `claude -p`를 한 번씩 부르고,
답변을 ko_check.check로 셉니다. 조건은 system prompt 없음(none)과
--condition 이름=경로로 준 파일들입니다. 파일은 두 `---` 사이의 규칙 블록만
system prompt로 보냅니다. 블록이 없으면 파일 전체를 보냅니다.

    python3 evals/run_reply_bench.py \
        --condition simple-english=evals/conditions/simple-english-2.1.1.md \
        --condition simple-korean=prompts/system-prompt.md \
        --runs 2 --out evals/results/reply-2026-10-29

결과 폴더에 답변 원문(<조건>/<질문id>-r<회차>.md)과 scores.json을 씁니다.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ko_check  # noqa: E402

FENCE = re.compile(r"^---[ \t]*$", re.M)


def rule_block(text):
    text = re.sub(r"^---\r?\n[\s\S]*?\r?\n---\r?\n?", "", text)
    fences = list(FENCE.finditer(text))
    if len(fences) < 2:
        return text.strip()
    return text[fences[0].end():fences[1].start()].strip()


def generate(prompt, system, model, effort):
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json",
           "--setting-sources", "",
           "--disallowedTools", "Bash,Read,Write,Edit,Glob,Grep,WebFetch,WebSearch"]
    if system:
        cmd += ["--append-system-prompt", system]
    if effort:
        cmd += ["--effort", effort]
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=300, cwd="/tmp")
    return extract_result(r.stdout)


def extract_result(stdout):
    try:
        data = json.loads(stdout)
    except Exception:  # noqa: BLE001
        return stdout.strip()
    if isinstance(data, dict):
        return data.get("result", "")
    for item in reversed(data):
        if isinstance(item, dict) and item.get("type") == "result":
            return item.get("result", "")
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", action="append", default=[], help="이름=system prompt 파일 경로")
    ap.add_argument("--scenarios", default=str(HERE / "reply_scenarios.json"))
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--effort", default="low")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    conditions = {"none": ""}
    for item in args.condition:
        name, path = item.split("=", 1)
        conditions[name] = rule_block(pathlib.Path(path).read_text(encoding="utf-8"))

    scenarios = json.loads(pathlib.Path(args.scenarios).read_text(encoding="utf-8"))
    out = pathlib.Path(args.out)
    scores = []
    total = len(scenarios) * len(conditions) * args.runs
    done = 0
    for cond, system in conditions.items():
        (out / cond).mkdir(parents=True, exist_ok=True)
        for run in range(1, args.runs + 1):
            for sc in scenarios:
                target = out / cond / f"{sc['id']}-r{run}.md"
                if target.exists():
                    text = target.read_text(encoding="utf-8")
                else:
                    text = generate(sc["prompt"], system, args.model, args.effort)
                    target.write_text(text, encoding="utf-8")
                done += 1
                print(f"[{done}/{total}] {cond} {sc['id']} r{run}: {len(text)}자", file=sys.stderr)
                scores.append({"condition": cond, "id": sc["id"], "run": run, **ko_check.check(text)})

    meta = {"model": args.model, "effort": args.effort, "runs": args.runs,
            "conditions": {k: (len(v) if v else 0) for k, v in conditions.items()}}
    (out / "scores.json").write_text(
        json.dumps({"meta": meta, "scores": scores}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"scores.json 저장: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
