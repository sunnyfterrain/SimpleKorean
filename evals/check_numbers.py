#!/usr/bin/env python3
"""측정 결과 폴더의 답변 원문에서 숫자를 다시 계산하고 README와 맞는지 확인합니다.

    python3 evals/check_numbers.py evals/results/reply-2026-10-29            # 표 출력
    python3 evals/check_numbers.py evals/results/reply-2026-10-29 --write    # RESULTS.md 갱신
    python3 evals/check_numbers.py evals/results/reply-2026-10-29 --check README.md

--check는 다시 계산한 표의 각 줄이 README.md와 결과 폴더의 RESULTS.md에
그대로 있는지 봅니다. 없으면 종료 코드 1입니다. CI가 push마다 돕니다.
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ko_check  # noqa: E402

ORDER = ["none", "simple-english", "simple-korean"]
LABEL = {"none": "style 없음", "simple-english": "simple-english 2.1.1", "simple-korean": "simple-korean 0.1.0"}

COLUMNS = [
    ("평균 어절", "words"),
    ("평균 문장", "sentences"),
    ("em-dash", "em_dash"),
    ("bold", "bold"),
    ("header", "header"),
    ("bullet", "bullet"),
    ("table 줄", "table_row"),
    ("여닫는 말", "opener_closer"),
    ("번역투", "translationese"),
    ("꾸밈말", "slop"),
    ("얼버무림", "hedge"),
]


def aggregate(folder):
    rows = {}
    for cond_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        files = sorted(cond_dir.glob("*.md"))
        if not files:
            continue
        results = [ko_check.check(f.read_text(encoding="utf-8")) for f in files]
        n = len(results)
        c = [r["counts"] for r in results]
        rows[cond_dir.name] = {
            "n": n,
            "words": sum(r["words"] for r in results) / n,
            "sentences": sum(r["sentences"] for r in results) / n,
            "em_dash": sum(x["em_dash"] for x in c),
            "bold": sum(x["bold"] for x in c),
            "header": sum(x["header"] for x in c),
            "bullet": sum(x["bullet"] for x in c),
            "table_row": sum(x["table_row"] for x in c),
            "opener_closer": sum(x["opener"] + x["closer"] for x in c),
            "translationese": sum(x["translationese"] for x in c),
            "slop": sum(x["slop"] for x in c),
            "hedge": sum(x["hedge"] for x in c),
        }
    return rows


def fmt(v):
    return f"{v:.1f}" if isinstance(v, float) else str(v)


def table(rows):
    head = "| 조건 | 답변 수 | " + " | ".join(name for name, _ in COLUMNS) + " |"
    sep = "|---|---:|" + "|".join("---:" for _ in COLUMNS) + "|"
    lines = [head, sep]
    for cond in ORDER + sorted(k for k in rows if k not in ORDER):
        if cond not in rows:
            continue
        r = rows[cond]
        lines.append(f"| {LABEL.get(cond, cond)} | {r['n']} | " + " | ".join(fmt(r[key]) for _, key in COLUMNS) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--write", action="store_true", help="결과 폴더의 RESULTS.md를 표로 갱신")
    ap.add_argument("--check", nargs="*", help="표의 각 줄이 이 파일들에 있는지 확인")
    args = ap.parse_args()

    folder = pathlib.Path(args.folder)
    rows = aggregate(folder)
    text = table(rows)
    print(text)

    meta_path = folder / "scores.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))["meta"] if meta_path.exists() else {}

    if args.write:
        body = [
            "# 답변 측정 결과",
            "",
            f"모델 `{meta.get('model', '?')}`, effort `{meta.get('effort', '?')}`, 질문 8개 × {meta.get('runs', '?')}회.",
            "숫자는 조건별 답변 전체의 합이고, 어절과 문장은 답변당 평균입니다.",
            "`python3 evals/check_numbers.py`가 이 폴더의 답변 원문에서 표를 다시 계산합니다.",
            "",
            text,
            "",
            "여닫는 말은 첫 문장의 여는 말과 본문의 닫는 말을 더한 수입니다.",
            "번역투는 `ko_check.py`의 여섯 패턴 합계, 꾸밈말은 금지어 목록 적중 수, 얼버무림은 \"것 같습니다\" 류의 수입니다.",
            "문장이 자연스러운지는 세지 못합니다.",
            "",
        ]
        (folder / "RESULTS.md").write_text("\n".join(body), encoding="utf-8")
        print(f"\nRESULTS.md 갱신: {folder / 'RESULTS.md'}", file=sys.stderr)

    if args.check is not None:
        targets = [pathlib.Path(p) for p in (args.check or [])] + [folder / "RESULTS.md"]
        missing = []
        data_lines = text.splitlines()[2:]
        for t in targets:
            content = t.read_text(encoding="utf-8") if t.exists() else ""
            for line in data_lines:
                if line not in content:
                    missing.append((str(t), line))
        if missing:
            print("\n다음 줄이 파일에 없거나 숫자가 다릅니다:", file=sys.stderr)
            for t, line in missing:
                print(f"  {t}: {line}", file=sys.stderr)
            return 1
        print("\n숫자 확인 통과", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
