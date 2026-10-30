<p align="center">
  <strong>AI가 쓴 한국어에서 번역투와 장식을 걷어 내고, 한 번 읽고 이해하는 문장만 남깁니다.</strong>
</p>

<p align="center">
  A Korean edition of <a href="https://github.com/AminBlg/SimpleEnglish">AminBlg/SimpleEnglish</a>: an agent skill and Claude Code output style that make LLMs write plain, one-read Korean.<br>
  Install: <code>npx skills add sunnyfterrain/SimpleKorean</code>
</p>

<p align="center">
  <a href="evals/results/reply-2026-10-29/RESULTS.md"><img src="https://img.shields.io/badge/measured-Claude_Sonnet_5.5-blueviolet?style=flat" alt="Claude Sonnet 5.5로 측정"></a>
  <a href="skills/simple-korean/SKILL.md"><img src="https://img.shields.io/badge/version-0.2.0-blue?style=flat" alt="version 0.2.0"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat" alt="MIT"></a>
</p>

[Agent Skills 표준](https://agentskills.io)을 읽는 에이전트(Claude Code, Cursor, Codex, Gemini CLI, OpenCode 등)에서 동작합니다.\
폴더 하나, 의존성 없음, MIT.

## 왜 만들었나

SimpleEnglish는 항공 정비 매뉴얼의 통제 언어 ASD-STE100으로 AI의 영어를 다듬습니다.\
한국어 출력에 그대로 쓰면 규칙의 절반이 헛돕니다.

관사, contraction, "should" 금지, 25단어 제한은 한국어에 대응물이 없습니다.\
한국어 AI 출력의 흔한 흔적인 번역투("~에 대하여", "~를 통해"), 근거 없는 얼버무림("~것 같습니다"), 확인과 추정을 섞는 어미는 영어 규칙이 잡지 못합니다.

이 저장소는 원본의 구조를 그대로 두고 규칙을 한국어 기준으로 다시 썼습니다.

## 설치

에이전트와 상관없이, [skills CLI](https://github.com/vercel-labs/skills)로 스킬만 설치합니다.

```bash
npx skills add sunnyfterrain/SimpleKorean
```

Claude Code 플러그인은 SessionStart hook까지 설치합니다.\
hook은 세션이 시작할 때마다 규칙을 넣으므로 스킬 이름을 부르지 않아도 됩니다.

```bash
claude plugin marketplace add sunnyfterrain/SimpleKorean && claude plugin install simple-korean@simple-korean
```

output style로 쓰려면 [`output-styles/simple-korean.md`](output-styles/simple-korean.md)를 `~/.claude/output-styles/`에 복사하고 `/config`의 Output style에서 `simple-korean`을 고르세요.

플러그인과 output style은 둘 중 하나만 쓰세요.\
둘 다 켜면 같은 규칙이 두 번 실립니다.\
hook은 settings에서 output style `simple-korean`을 찾으면 규칙을 넣지 않고 안내 한 줄만 출력합니다.

스킬을 지원하지 않는 도구라면 [`prompts/system-prompt.md`](prompts/system-prompt.md)의 규칙 블록을 system prompt, `AGENTS.md`, `.cursorrules`에 붙이세요.\
같은 페이지 끝에 짧은 판본도 있습니다.

## 예시

같은 질문에 대한 실제 Claude 출력이고, 글자는 고치지 않았습니다.\
표 칸 안에서 줄을 바꾸려고 문단 안의 줄바꿈만 `<br>`로 바꿨습니다.

질문: "React에서 useEffect가 두 번 실행돼요. 버그인가요?"

| | 적용 전 | 적용 후 |
|---|---:|---:|
| 어절 | 193 | 79 |
| bold | 6 | 0 |
| header | 5 | 0 |
| bullet | 5 | 0 |

<table>
<tr>
<th width="50%">적용 전</th>
<th width="50%">적용 후 (0.2.0)</th>
</tr>
<tr>
<td valign="top">

버그가 아닙니다. 대부분 **React 18+ Strict Mode**의 의도된 동작입니다.

## 원인

개발 환경(`npm run dev`)에서 `<React.StrictMode>`로 감싸면, React가 컴포넌트를 마운트 → 언마운트 → 재마운트 순으로 한 번 더 시뮬레이션합니다. 그래서 `useEffect`가 (setup → cleanup → setup) 순서로 실행됩니다.

- **프로덕션 빌드에서는 한 번만** 실행됩니다.
- 목적은 cleanup이 빠졌거나 effect가 멱등적이지 않은 버그를 개발 중에 미리 드러내는 것입니다.

## 확인 방법

```jsx
useEffect(() => {
  console.log('setup');
  return () => console.log('cleanup');
}, []);
```

개발 모드에서 `setup → cleanup → setup`이 찍히면 Strict Mode 때문입니다.

## 올바른 대응

Strict Mode를 끄지 말고, **effect를 cleanup 가능하게** 작성하세요.

```jsx
useEffect(() => {
  const conn = createConnection();
  conn.connect();
  return () => conn.disconnect();   // 구독/타이머/리스너 정리
}, []);
```

데이터 fetch는 취소 처리를 해주세요.

```jsx
useEffect(() => {
  const controller = new AbortController();
  fetch(url, { signal: controller.signal })
    .then(r => r.json())
    .then(setData)
    .catch(e => { if (e.name !== 'AbortError') throw e; });
  return () => controller.abort();
}, [url]);
```

(실무에서는 TanStack Query, SWR 같은 라이브러리나 Suspense 기반 데이터 로딩을 쓰면 이 문제를 신경 쓸 일이 줄어듭니다.)

## Strict Mode가 아닌 경우 점검할 것

1. **의존성 배열이 매 렌더마다 바뀜**: 객체/배열/함수를 deps에 넣으면 매번 새 참조라 effect가 반복 실행됩니다. `useMemo`/`useCallback`으로 안정화하거나 effect 안으로 옮기세요.
2. **컴포넌트가 실제로 두 번 마운트됨**: 부모의 `key` 변경, 조건부 렌더링, 라우터 전환 등으로 언마운트/마운트가 일어나는지 확인하세요.
3. **effect 안에서 state를 바꿔 다시 트리거**: deps에 있는 state를 effect가 갱신하면 연쇄 실행됩니다.

## 하지 말아야 할 것

`useRef`로 "이미 실행됨" 플래그를 두어 두 번째 실행을 막는 방식은 임시방편입니다. 문제를 가릴 뿐 근본 원인(cleanup 누락)을 해결하지 못합니다.

---

코드를 보여주시면 Strict Mode 때문인지, 다른 원인인지 구체적으로 짚어드릴 수 있습니다.

</td>
<td valign="top">

버그가 아닙니다.<br>
React 18 이상에서 개발 모드의 StrictMode가 일부러 effect를 두 번 실행합니다.

mount, unmount, mount 순서로 한 번 더 돌려서 cleanup이 빠진 effect를 찾아내려는 동작입니다.<br>
프로덕션 빌드에서는 한 번만 실행됩니다.

두 번 실행돼서 문제가 생긴다면 effect에 cleanup이 없다는 신호입니다.<br>
구독, 타이머, 이벤트 리스너는 cleanup 함수에서 해제하세요.

```jsx
useEffect(() => {
  const id = setInterval(tick, 1000);
  return () => clearInterval(id);
}, []);
```

fetch는 `AbortController`로 이전 요청을 취소하거나 `ignore` 플래그로 늦게 온 응답을 무시하세요.

```jsx
useEffect(() => {
  let ignore = false;
  fetch(url).then(r => r.json()).then(data => {
    if (!ignore) setData(data);
  });
  return () => { ignore = true; };
}, [url]);
```

StrictMode를 끄면 증상은 사라지지만 버그를 숨기는 셈입니다.<br>
프로덕션에서도 두 번 실행된다면 컴포넌트가 실제로 두 번 mount되는 것이니, `key` 변경이나 부모의 조건부 렌더링을 확인하세요.

</td>
</tr>
</table>

원문은 [적용 전](evals/results/readme-example-2026-10-30/candidates/none/useeffect.md)과 [적용 후](evals/results/readme-example-2026-10-30/candidates/simple-korean-0.2.0/useeffect.md)에 있습니다.\
모델은 둘 다 `claude-sonnet-5-5`, effort low이고, 적용 후는 0.2.0 규칙입니다.\
같은 폴더에 다른 후보 질문 두 개(rebase와 merge, 기획자에게 장애 설명)의 답도 있습니다.

런북, 에러 메시지, commit message, 작업 보고 예시는 [`examples/before-after.md`](examples/before-after.md)에 있습니다.

## 측정

채팅 질문 8개를 두 번씩 물어 조건마다 답변 16개를 받았습니다.\
이 측정은 0.1.0 기준이고, 0.2.0에서 추가한 줄바꿈 규칙은 아직 측정하지 않았습니다.

- 질문: 원본 SimpleEnglish의 8개를 한국어로 옮겼습니다. 질문마다 영어 기술 용어가 하나씩 들어 있습니다.
- 모델: `claude-sonnet-5-5`, effort low, 설정 파일은 읽지 않았습니다.
- 집계: 16개 답변의 합계입니다. 어절과 문장만 답변당 평균입니다.

답변 원문과 표는 [RESULTS.md](evals/results/reply-2026-10-29/RESULTS.md)에 있습니다.

| 항목 | style 없음 | simple-english 2.1.1 | simple-korean 0.1.0 |
|---|---:|---:|---:|
| 답변 수 | 16 | 16 | 16 |
| 평균 어절 | 257.4 | 194.5 | 188.6 |
| 평균 문장 | 20.8 | 17.1 | 20.0 |
| em-dash | 1 | 0 | 0 |
| bold | 129 | 0 | 0 |
| header | 74 | 0 | 0 |
| bullet | 188 | 0 | 51 |
| table 줄 | 28 | 0 | 0 |
| 여닫는 말 | 0 | 0 | 0 |
| 번역투 | 11 | 4 | 4 |
| 꾸밈말 | 2 | 0 | 0 |
| 얼버무림 | 1 | 0 | 0 |

규칙을 넣으면 bold, header, table이 사라졌습니다.\
규칙이 없을 때는 답변 16개에 bold 129개, header 74개, table 줄 28개가 있었습니다.\
두 규칙 모두 이것을 0으로 만들었습니다.

simple-korean은 bullet을 51개 남겼습니다.\
대등한 항목이 셋 이상이면 목록을 허용하기 때문입니다.\
목록 13개 가운데 12개는 항목이 셋 이상이거나 코드 블록으로 나뉜 번호 단계였습니다.

1개(`why-timeout-r1`)는 항목 둘을 bullet으로 써서 규칙을 어겼습니다.

답변 길이는 평균 257어절에서 189어절로 줄었습니다.\
번역투는 11개에서 4개로 줄었고, 남은 4개는 모두 "구체적인", "표준적인" 같은 "~적인"입니다.

영어 판 simple-english를 한국어 질문에 써도 숫자는 거의 같았습니다.\
이 측정이 보여 주는 두 판본의 차이는 목록 허용 여부 하나입니다.\
문장이 얼마나 자연스러운지는 regex로 세지 못해서 이 표에 없습니다.

여는 말과 닫는 말, em-dash는 규칙이 없을 때도 거의 나오지 않았습니다.\
Sonnet 5.5의 한국어 답변에는 원래 드문 흔적이라 이 측정에서는 차이를 보여 주지 못합니다.

## 규칙

규칙의 원본은 [`skills/simple-korean/SKILL.md`](skills/simple-korean/SKILL.md)입니다.\
output style과 system prompt는 그 축약판입니다.\
규칙은 두 register로 나뉩니다.

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
| 한 문장마다 줄바꿈, 문단 사이 빈 줄 | 화면 끝까지 이어지는 한 줄짜리 문단 |

## 원본과 다른 점

| 항목 | SimpleEnglish | SimpleKorean |
|---|---|---|
| 답변 서식 | header, bullet, bold, table 모두 금지 | 비교하거나 셀 때만 허용 |
| 문장 길이 | 단어 수 제한(20/25단어) | 문장당 새 정보 하나 |
| Strict mode | STE 영어 사전 적용 | 없음 |
| 줄바꿈 | 규칙 없음 | 한 문장마다 줄바꿈, 문단 사이 빈 줄 |
| commit message | 영어 | 한국어, 제목은 명사형 |

서식을 조건부로 허용한 것은 한국어 독자가 비교할 때 표와 목록을 더 빨리 읽는다는 판단 때문입니다.\
목록은 항목 셋 이상, table은 비교 대상 둘 이상에 비교 축 둘 이상, header는 답이 세 부분 이상, bold는 문단당 한 구절일 때 씁니다.

문장 길이를 단어 수로 제한하지 않은 것은 한국어 어절 수가 정보량을 잘 반영하지 못하기 때문입니다.\
Strict mode가 없는 것은 한국어에 STE 사전에 해당하는 표준 사전이 없기 때문입니다.

## 아직 없는 것

측정은 Claude Sonnet 5.5 한 모델, 답변 register 하나뿐입니다.\
문서 register 측정, 다른 모델, 다른 회사 모델 측정은 아직 없습니다.

문장이 자연스러운지는 측정하지 않았습니다.\
`evals/ko_check.py`는 regex로 셀 수 있는 것만 셉니다.

원본처럼 두 판본을 블라인드로 비교 판정하는 단계는 다음 버전에 넣을 계획입니다.

원본의 PostToolUse linter hook에 해당하는 것이 없습니다.\
원본 Issue [#41](https://github.com/AminBlg/SimpleEnglish/issues/41)처럼 linter가 맞는 문장을 고치게 만드는 문제를 피하려고, 검사기는 측정에만 씁니다.

## 기여

질문과 버그는 issue로 올려 주세요.\
Pull request를 환영합니다.\
측정 숫자를 바꾸는 변경은 답변 원문을 함께 올려 주세요.\
push 전에 다음을 실행하세요.

```bash
cd src/hooks && node --test && cd ../..
python3 evals/ko_check.py --self-test
python3 evals/check_numbers.py evals/results/reply-2026-10-29 --check README.md
```

## 출처와 라이선스

이 저장소는 [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish)(MIT, Copyright (c) 2026 AminBlg)의 저장소 구조, SessionStart hook, 측정 방식을 바탕으로 만들었습니다.

hook 스크립트는 원본을 가져와 고쳤고, 규칙과 나머지 파일은 새로 썼습니다.\
비교 측정용으로 원본의 `prompts/system-prompt.md`(2.1.1)를 [`evals/conditions/`](evals/conditions/)에 그대로 두었습니다.

MIT. 비공식 프로젝트이고, 원본 저자나 ASD와 관계없습니다.
