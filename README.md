<p align="center">
  <strong>AI가 쓴 한국어에서 번역투와 장식을 걷어 내고, 한 번 읽고 이해하는 문장만 남깁니다.</strong>
</p>

<p align="center">
  A Korean edition of <a href="https://github.com/AminBlg/SimpleEnglish">AminBlg/SimpleEnglish</a>: an agent skill and Claude Code output style that make LLMs write plain, one-read Korean.<br>
  Install: <code>npx skills add sunnyfterrain/SimpleKorean</code>
</p>

<p align="center">
  <a href="evals/results/reply-2026-10-29/RESULTS.md"><img src="https://img.shields.io/badge/measured-Claude_Sonnet_5.5-blueviolet?style=flat" alt="Claude Sonnet 5.5로 측정"></a>
  <a href="skills/simple-korean/SKILL.md"><img src="https://img.shields.io/badge/version-0.1.0-blue?style=flat" alt="version 0.1.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat" alt="MIT"></a>
</p>

[Agent Skills 표준](https://agentskills.io)을 읽는 에이전트(Claude Code, Cursor, Codex, Gemini CLI, OpenCode 등)에서 동작합니다. 폴더 하나, 의존성 없음, MIT.

## 왜 만들었나

SimpleEnglish는 항공 정비 매뉴얼의 통제 언어 ASD-STE100으로 AI의 영어를 다듬습니다. 한국어 출력에 그대로 쓰면 규칙의 절반이 헛돕니다. 관사, contraction, "should" 금지, 25단어 제한은 한국어에 대응물이 없습니다. 한국어 AI 출력의 흔한 흔적인 번역투("~에 대하여", "~를 통해"), 근거 없는 얼버무림("~것 같습니다"), 확인과 추정을 섞는 어미는 영어 규칙이 잡지 못합니다. 이 저장소는 원본의 구조를 그대로 두고 규칙을 한국어 기준으로 다시 썼습니다.

## 설치

에이전트와 상관없이, [skills CLI](https://github.com/vercel-labs/skills)로 스킬만 설치합니다.

```bash
npx skills add sunnyfterrain/SimpleKorean
```

Claude Code 플러그인은 SessionStart hook까지 설치합니다. hook은 세션이 시작할 때마다 규칙을 넣으므로 스킬 이름을 부르지 않아도 됩니다.

```bash
claude plugin marketplace add sunnyfterrain/SimpleKorean && claude plugin install simple-korean@simple-korean
```

output style로 쓰려면 [`output-styles/simple-korean.md`](output-styles/simple-korean.md)를 `~/.claude/output-styles/`에 복사하고 `/config`의 Output style에서 `simple-korean`을 고르세요.

플러그인과 output style은 둘 중 하나만 쓰세요. 둘 다 켜면 같은 규칙이 두 번 실립니다. hook은 settings에서 output style `simple-korean`을 찾으면 규칙을 넣지 않고 안내 한 줄만 출력합니다.

스킬을 지원하지 않는 도구라면 [`prompts/system-prompt.md`](prompts/system-prompt.md)의 규칙 블록을 system prompt, `AGENTS.md`, `.cursorrules`에 붙이세요. 같은 페이지 끝에 짧은 판본도 있습니다.

## 예시

왼쪽은 규칙 없는 답, 오른쪽은 규칙을 적용한 답입니다.

<table>
<tr>
<th width="50%">적용 전</th>
<th width="50%">적용 후</th>
</tr>
<tr>
<td valign="top">

> 좋은 질문입니다! idempotent에 대해 설명드리겠습니다.
>
> **Idempotent(멱등성)**란 동일한 요청을 여러 번 수행해도 결과가 동일하게 유지되는 특성을 의미합니다. 즉, 재시도를 통해 발생할 수 있는 부작용이 없다는 것을 보장하는 매우 중요한 개념입니다.
>
> 도움이 되셨길 바랍니다!

</td>
<td valign="top">

> 안전합니다. idempotent(두 번 보내도 결과가 같음)한 endpoint는 같은 요청을 다시 받아도 주문을 하나만 만듭니다. 그래서 timeout 뒤 재시도가 중복 주문을 만들지 않습니다.

</td>
</tr>
</table>

런북, 에러 메시지, commit message, 작업 보고 예시는 [`examples/before-after.md`](examples/before-after.md)에 있습니다.

## 측정

채팅 질문 8개를 두 번씩 물어 조건마다 답변 16개를 받았습니다. 질문은 원본 SimpleEnglish의 8개를 한국어로 옮긴 것이고, 각 질문에 영어 기술 용어가 하나씩 들어 있습니다. 모델은 `claude-sonnet-5-5`, effort low, 설정 파일은 읽지 않았습니다. 숫자는 16개 답변의 합계이고, 어절과 문장만 답변당 평균입니다. [원문과 표](evals/results/reply-2026-10-29/RESULTS.md)

| 조건 | 답변 수 | 평균 어절 | 평균 문장 | em-dash | bold | header | bullet | table 줄 | 여닫는 말 | 번역투 | 꾸밈말 | 얼버무림 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| style 없음 | 16 | 257.4 | 20.8 | 1 | 129 | 74 | 188 | 28 | 0 | 11 | 2 | 1 |
| simple-english 2.1.1 | 16 | 194.5 | 17.1 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| simple-korean 0.1.0 | 16 | 188.6 | 20.0 | 0 | 0 | 0 | 51 | 0 | 0 | 4 | 0 | 0 |

규칙을 넣으면 bold, header, table이 사라졌습니다. 규칙이 없을 때는 답변 16개에 bold 129개, header 74개, table 줄 28개가 있었습니다. 두 규칙 모두 이것을 0으로 만들었습니다.

simple-korean은 bullet을 51개 남겼습니다. 대등한 항목이 셋 이상이면 목록을 허용하기 때문입니다. 목록 13개 가운데 12개는 항목이 셋 이상이거나 코드 블록으로 나뉜 번호 단계였습니다. 1개(`why-timeout-r1`)는 항목 둘을 bullet으로 써서 규칙을 어겼습니다.

답변 길이는 평균 257어절에서 189어절로 줄었습니다. 번역투는 11개에서 4개로 줄었고, 남은 4개는 모두 "구체적인", "표준적인" 같은 "~적인"입니다.

영어 판 simple-english를 한국어 질문에 써도 숫자는 거의 같았습니다. 이 측정이 보여 주는 두 판본의 차이는 목록 허용 여부 하나입니다. 문장이 얼마나 자연스러운지는 regex로 세지 못해서 이 표에 없습니다.

여는 말과 닫는 말, em-dash는 규칙이 없을 때도 거의 나오지 않았습니다. Sonnet 5.5의 한국어 답변에는 원래 드문 흔적이라 이 측정에서는 차이를 보여 주지 못합니다.

## 규칙

규칙의 원본은 [`skills/simple-korean/SKILL.md`](skills/simple-korean/SKILL.md)입니다. output style과 system prompt는 그 축약판입니다. 규칙은 두 register로 나뉩니다.

공통 규칙과 문서 register:

| 규칙 | 없애는 것 |
|---|---|
| 한 문장에 새 정보 하나 | 숫자와 조건을 한 문장에 몰아넣은 문장 |
| 능동형, 행위자 명시 | "실행됩니다", "처리되었습니다"의 주어 없는 문장 |
| 번역투 금지 | "~에 대하여", "~되어지다", "~를 통해", "~에 있어서" |
| 어미로 확인 수위 구분 | 들은 말을 확인한 사실처럼 쓰는 문장 |
| em-dash와 세미콜론 금지 | 영어 문장 부호로 이어 붙인 반쪽 생각 |
| 사실을 쓰고 중요성은 빼기 | "원활하게", "강력한", "매우 중요한" |
| 기술 용어는 영어 그대로 | "훅", "커밋", "엔드포인트" 같은 음차 |
| 조건을 명령 앞에 | 실행하고 나서야 읽게 되는 "...한 경우에" |

답변 register:

| 규칙 | 없애는 것 |
|---|---|
| 첫 문장이 답 | 질문 되풀이와 예열 문장 |
| 여닫는 말 금지 | "좋은 질문입니다", "도움이 되셨길 바랍니다" |
| 서식은 비교하거나 셀 때만 | 한 줄 답을 둘러싼 header, bullet, bold |

## 원본과 다른 점

서식을 금지하지 않고 조건부로 허용합니다. 원본은 답변에서 header, bullet, bold, table을 모두 금지합니다. 한국어 독자는 대등한 항목이 많거나 비교가 필요할 때 표와 목록을 더 빨리 읽는다는 판단입니다. 기준은 이렇습니다. 목록은 항목 셋 이상, table은 비교 대상 둘 이상에 비교 축 둘 이상, header는 답이 세 부분 이상일 때, bold는 문단당 한 구절.

문장 길이를 단어 수로 제한하지 않습니다. 한국어는 어절 수가 정보량을 잘 반영하지 못합니다. 대신 문장당 새 정보 하나로 제한합니다.

Strict mode가 없습니다. 원본의 Strict mode는 STE 영어 사전을 적용하는데, 한국어에는 대응하는 표준 사전이 없습니다.

commit message를 한국어로 씁니다. 제목은 명사형으로 끝내고 본문은 "~합니다" 체 산문입니다.

## 아직 없는 것

측정은 Claude Sonnet 5.5 한 모델, 답변 register 하나뿐입니다. 문서 register 측정, 다른 모델, 다른 회사 모델 측정은 아직 없습니다.

문장이 자연스러운지는 측정하지 않았습니다. `evals/ko_check.py`는 regex로 셀 수 있는 것만 셉니다. 원본처럼 두 판본을 블라인드로 비교 판정하는 단계는 다음 버전에 넣을 계획입니다.

원본의 PostToolUse linter hook에 해당하는 것이 없습니다. 원본 Issue [#41](https://github.com/AminBlg/SimpleEnglish/issues/41)처럼 linter가 맞는 문장을 고치게 만드는 문제를 피하려고, 검사기는 측정에만 씁니다.

## 기여

질문과 버그는 issue로 올려 주세요. Pull request를 환영합니다. 측정 숫자를 바꾸는 변경은 답변 원문을 함께 올려 주세요. push 전에 다음을 실행하세요.

```bash
cd src/hooks && node --test && cd ../..
python3 evals/ko_check.py --self-test
python3 evals/check_numbers.py evals/results/reply-2026-10-29 --check README.md
```

## 출처와 라이선스

이 저장소는 [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish)(MIT, Copyright (c) 2026 AminBlg)의 저장소 구조, SessionStart hook, 측정 방식을 바탕으로 만들었습니다. hook 스크립트는 원본을 가져와 고쳤고, 규칙과 나머지 파일은 새로 썼습니다. 비교 측정용으로 원본의 `prompts/system-prompt.md`(2.1.1)를 [`evals/conditions/`](evals/conditions/)에 그대로 두었습니다.

MIT. 비공식 프로젝트이고, 원본 저자나 ASD와 관계없습니다.
