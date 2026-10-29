curl이 서버의 인증서를 발급한 CA(인증기관)를 신뢰 목록에서 찾지 못했다는 뜻입니다. 사내 API는 보통 사내 CA가 발급한 인증서를 쓰는데, curl이 쓰는 CA 목록에 그 사내 CA가 없어서 생깁니다. 사내 프록시가 HTTPS를 가로채 자체 인증서로 다시 서명하는 환경에서도 같은 에러가 납니다.

고치는 방법은 사내 CA 인증서를 curl에 알려주는 것입니다.

1. IT팀이나 사내 위키에서 루트 CA 인증서(.crt 또는 .pem)를 받으세요.
2. 한 번만 테스트하려면 `curl --cacert /path/to/company-ca.pem https://api.example.com`으로 실행하세요.
3. 계속 쓰려면 `export CURL_CA_BUNDLE=/path/to/company-ca.pem`을 ~/.zshrc에 추가하세요.
4. macOS 시스템 curl은 키체인을 쓰므로, 키체인 접근에서 사내 CA를 "항상 신뢰"로 지정해도 됩니다. Homebrew curl은 키체인을 보지 않으니 2번이나 3번을 쓰세요.

서버가 중간 인증서(intermediate)를 빠뜨리고 보내는 경우도 같은 에러가 납니다. 이때는 `openssl s_client -connect api.example.com:443 -showcerts`로 서버가 보내는 체인을 확인하고, 서버 담당자에게 체인 전체를 설정해 달라고 요청하세요.

`curl -k`(검증 끄기)는 중간자 공격에 노출되므로 임시 확인 외에는 쓰지 마세요.

원인이 어느 쪽인지 알려주시면 더 좁혀 드리겠습니다. 호스트 이름을 주시면 제가 인증서 체인을 직접 확인해 볼 수도 있습니다.