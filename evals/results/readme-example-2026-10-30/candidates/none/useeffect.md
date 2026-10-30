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