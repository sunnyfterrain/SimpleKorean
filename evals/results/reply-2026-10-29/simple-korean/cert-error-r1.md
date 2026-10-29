사내 API 서버의 인증서를 발급한 CA(인증 기관)를 curl이 신뢰 목록에서 찾지 못해서 생기는 오류입니다. 사내 API는 보통 회사 내부 CA가 서명한 인증서를 쓰기 때문에, 공인 CA만 담긴 기본 목록으로는 인증서 체인을 끝까지 검증할 수 없습니다. 서버가 중간 인증서(intermediate)를 빠뜨리고 보내거나, 회사 프록시가 TLS 트래픽을 가로채 자체 인증서로 다시 서명하는 경우에도 같은 오류가 납니다.

먼저 서버가 어떤 체인을 보내는지 확인하세요. `api.example.internal`은 실제 호스트로 바꾸세요.

```sh
openssl s_client -connect api.example.internal:443 -showcerts </dev/null
```

출력의 `issuer`가 사내 CA 이름이면 CA 인증서가 없는 경우이고, 체인에 인증서가 하나뿐이면 서버가 중간 인증서를 보내지 않는 경우입니다. 후자는 서버 담당자에게 체인 전체를 설정하도록 요청해야 합니다.

사내 CA인 경우 해결 방법은 두 가지입니다.

1. 한 번만 쓸 때는 사내 루트 CA 파일(PEM)을 받아 curl에 직접 지정하세요.
   ```sh
   curl --cacert /path/to/company-root-ca.pem https://api.example.internal/health
   ```
2. 계속 쓸 때는 macOS 키체인에 CA를 신뢰 등록하세요.
   ```sh
   sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain /path/to/company-root-ca.pem
   ```
   Homebrew로 설치한 curl이나 Python, Node 등은 키체인을 읽지 않을 수 있습니다. 이 경우 `CURL_CA_BUNDLE`, `SSL_CERT_FILE`, `NODE_EXTRA_CA_CERTS` 같은 환경 변수로 CA 파일을 지정하세요.

사내 CA 파일은 IT팀이나 인프라팀에 문의하면 받을 수 있습니다. `curl -k`(검증 끄기)는 오류를 없애 주지만 중간자 공격을 막지 못하므로, 원인 확인용으로만 쓰고 스크립트나 운영 환경에는 넣지 마세요.