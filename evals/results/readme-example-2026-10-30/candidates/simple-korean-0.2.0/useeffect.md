버그가 아닙니다.
React 18 이상에서 개발 모드의 StrictMode가 일부러 effect를 두 번 실행합니다.

mount, unmount, mount 순서로 한 번 더 돌려서 cleanup이 빠진 effect를 찾아내려는 동작입니다.
프로덕션 빌드에서는 한 번만 실행됩니다.

두 번 실행돼서 문제가 생긴다면 effect에 cleanup이 없다는 신호입니다.
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

StrictMode를 끄면 증상은 사라지지만 버그를 숨기는 셈입니다.
프로덕션에서도 두 번 실행된다면 컴포넌트가 실제로 두 번 mount되는 것이니, `key` 변경이나 부모의 조건부 렌더링을 확인하세요.