# Changelog

## 0.1.0 (2026-10-29)

첫 공개 버전입니다.

- `skills/simple-korean/SKILL.md`: 규칙의 원본
- `output-styles/simple-korean.md`: Claude Code output style 축약판
- `prompts/system-prompt.md`: 스킬을 읽지 못하는 도구용 규칙 블록과 짧은 판본
- Claude Code 플러그인: SessionStart hook이 규칙 블록을 세션에 넣음. output style이 켜져 있으면 중복 주입을 건너뜀
- `evals/`: 답변 측정 도구(`ko_check.py`, `run_reply_bench.py`, `check_numbers.py`)와 측정 결과
- `examples/before-after.md`: 적용 전후 예시
