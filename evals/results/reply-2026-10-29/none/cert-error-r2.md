## 무슨 일인가

curl이 서버가 보낸 인증서 체인을 **신뢰할 수 있는 루트 CA까지 연결하지 못했다**는 뜻입니다. 대부분 사내 API는 다음 중 하나입니다.

1. **사내 사설 CA**로 서명한 인증서를 쓰는데, 내 맥의 신뢰 저장소(또는 curl이 쓰는 CA 번들)에 그 CA가 없는 경우
2. **회사 프록시/보안 장비(SSL 인스펙션)**가 TLS를 가로채 자체 CA로 재서명하는 경우
3. 서버가 **중간 인증서(intermediate)를 빠뜨리고** 리프 인증서만 보내는 경우

## 진단

```sh
# 서버가 보내는 체인과 발급자 확인
openssl s_client -connect api.example.internal:443 -showcerts </dev/null 2>/dev/null | grep -E 's:|i:'
```

- 발급자(`i:`)가 사내 CA 이름이면 → 1번 또는 2번
- 체인이 리프 하나뿐이고 `verify error:num=20/21`이 보이면 → 3번

## 해결

**올바른 방법: 사내 루트 CA를 신뢰시키기**

사내 루트 CA 인증서(`.pem`/`.crt`)를 IT/보안팀에서 받은 뒤:

```sh
# 1) 이번 호출에만 지정
curl --cacert /path/to/company-root-ca.pem https://api.example.internal/...

# 2) 항상 쓰도록 환경변수 지정 (~/.zshrc)
export CURL_CA_BUNDLE=/path/to/company-root-ca.pem
export SSL_CERT_FILE=/path/to/company-root-ca.pem
```

macOS 키체인에 등록하는 방법도 있습니다(Safari/시스템 앱용).

```sh
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain /path/to/company-root-ca.pem
```

다만 Homebrew curl이나 OpenSSL 기반 curl은 키체인을 안 보고 자체 번들을 쓰므로 `--cacert`가 더 확실합니다. 번들에 사내 CA를 추가하려면 `cat company-root-ca.pem >> $(brew --prefix)/etc/ca-certificates/cert.pem`처럼 이어 붙이면 됩니다. 단, brew 업데이트 시 덮어써질 수 있습니다.

**서버 문제(3번)라면**: 서버/로드밸런서 관리자에게 fullchain(리프+중간 인증서)을 설정하도록 요청하세요.

## 피해야 할 것

`curl -k` / `--insecure`는 인증서 검증을 통째로 끕니다. 임시 확인용으로는 되지만, 중간자 공격에 무방비가 되므로 스크립트나 운영 환경에는 쓰지 마세요.

---

어떤 호스트인지, 위 `openssl s_client` 출력이 어떻게 나오는지 알려주시면 원인을 더 정확히 짚어드릴 수 있습니다. 원하시면 제가 이 머신에서 직접 진단 명령을 돌려볼 수도 있습니다.