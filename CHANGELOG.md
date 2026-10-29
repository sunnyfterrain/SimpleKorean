# Changelog

## 0.2.0 (2026-10-29)

- 답변: 문단은 세 문장 이내, 문단 사이에 빈 줄, 문단 안에서는 한 문장마다 줄바꿈
- 문서: md 파일과 commit 본문은 한 문장마다 줄바꿈(semantic line breaks), 문단 사이에 빈 줄
- code block, table, 목록 항목 안에는 줄바꿈 규칙을 적용하지 않음
- 측정 결과는 0.1.0 기준으로 남김

## 0.1.0 (2026-10-29)

첫 공개 버전입니다.

- `skills/simple-korean/SKILL.md`: 규칙의 원본
- `output-styles/simple-korean.md`: Claude Code output style 축약판
- `prompts/system-prompt.md`: 스킬을 읽지 못하는 도구용 규칙 블록과 짧은 판본
- Claude Code 플러그인: SessionStart hook이 규칙 블록을 세션에 넣음. output style이 켜져 있으면 중복 주입을 건너뜀
- `evals/`: 답변 측정 도구(`ko_check.py`, `run_reply_bench.py`, `check_numbers.py`)와 측정 결과
- `examples/before-after.md`: 적용 전후 예시
