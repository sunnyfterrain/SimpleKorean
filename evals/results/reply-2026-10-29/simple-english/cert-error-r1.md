이 오류는 curl이 서버 인증서를 발급한 인증기관(CA, 인증서에 서명하는 기관)을 신뢰 목록에서 찾지 못했다는 뜻입니다. 사내 API는 보통 회사 자체 CA나 TLS 검사 프록시의 인증서를 쓰는데, 이 CA는 curl이 쓰는 공개 CA 번들에 없습니다. 서버가 중간 인증서를 보내지 않는 경우에도 같은 오류가 납니다.

먼저 서버가 보내는 인증서 체인을 확인하세요. 아래 명령에서 `api.example.internal`은 실제 호스트로 바꾸세요.

```
openssl s_client -connect api.example.internal:443 -showcerts </dev/null
```

출력의 `Verify return code`와 발급자(`issuer`) 이름을 보면 어느 CA가 문제인지 알 수 있습니다. 발급자가 회사 이름이면 원인은 사내 CA 미등록입니다.

해결은 회사 루트 CA 인증서(PEM 형식)를 받아서 curl에 알려주는 것입니다. IT 부서나 사내 위키에서 받을 수 있습니다. 한 번만 쓸 때는 옵션으로 지정합니다.

```
curl --cacert ~/certs/company-root-ca.pem https://api.example.internal/health
```

매번 쓰려면 환경 변수를 `~/.zshrc`에 넣습니다. 이 방법은 공개 CA를 모두 대체하므로, 기존 번들에 사내 CA를 이어 붙인 파일을 쓰는 편이 안전합니다.

```
cat "$(curl-config --ca)" ~/certs/company-root-ca.pem > ~/certs/combined.pem
export CURL_CA_BUNDLE=~/certs/combined.pem
```

Homebrew로 설치한 curl은 macOS 키체인을 읽지 않고 자체 번들을 씁니다. 사내 CA를 키체인에 이미 설치했는데도 오류가 나면 이 점이 원인일 수 있고, 위 방법이 해결책입니다. 시스템 기본 `/usr/bin/curl`로 같은 요청을 해 보면 차이를 확인할 수 있습니다.

`curl -k`는 인증서 검증을 완전히 끄므로 원인 확인용 임시 테스트에만 쓰세요. 스크립트나 운영 환경에는 넣지 마세요. 중간자 공격(통신 중간에서 내용을 가로채는 공격)을 막지 못합니다.

만약 체인에 중간 인증서가 빠져 있다면 클라이언트 설정이 아니라 서버 쪽 수정이 필요합니다. 이 경우 API 담당 팀에 서버가 중간 인증서까지 함께 보내도록 요청하세요.