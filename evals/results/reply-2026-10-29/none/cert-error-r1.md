**무슨 일인가요**

curl이 서버가 보낸 인증서 체인을 검증하다가, 그 인증서를 발급한 CA(발급자)를 자신의 신뢰 저장소(CA 번들)에서 찾지 못했다는 뜻입니다. 사내 API에서 흔한 원인은 다음과 같습니다.

1. **사내 사설 CA(Private CA)로 서명된 인증서**: 공인 CA가 아니라서 기본 번들에 없습니다. 가장 흔한 경우입니다.
2. **중간 인증서 누락**: 서버가 leaf 인증서만 보내고 intermediate를 빼먹은 경우입니다.
3. **회사 프록시/SSL 인스펙션**(Zscaler, Palo Alto 등): 중간에서 인증서를 재서명하는데, 그 루트 CA가 curl 번들에는 없습니다. 브라우저는 OS에 설치된 루트를 쓰기 때문에 잘 되는데 curl만 안 되는 경우가 많습니다.
4. 자체 서명 인증서

**진단**

```sh
# 서버가 보내는 체인과 발급자 확인
openssl s_client -connect api.internal.example.com:443 -showcerts </dev/null

# curl이 쓰는 CA 번들 위치 확인
curl -v https://api.internal.example.com 2>&1 | grep -i -E "CAfile|CApath"
```

출력의 `issuer`가 사내 CA 이름이면 1번 또는 3번, `verify error:num=21` 같은 에러가 보이면 2번(중간 인증서 누락)일 가능성이 큽니다.

**해결 방법 (권장 순서)**

1. **사내 루트 CA를 지정해서 사용** (가장 안전)
   IT/보안팀에서 루트 CA 인증서(`.pem`)를 받아서:
   ```sh
   curl --cacert /path/to/company-root-ca.pem https://api.internal.example.com
   # 또는 환경변수
   export CURL_CA_BUNDLE=/path/to/company-root-ca.pem
   ```

2. **macOS 키체인에 이미 사내 CA가 있다면** 그 인증서를 내보내서 사용합니다.
   ```sh
   security find-certificate -a -c "회사CA이름" -p /Library/Keychains/System.keychain > ~/company-ca.pem
   curl --cacert ~/company-ca.pem https://...
   ```
   Homebrew curl이라면 OS 저장소를 쓰는 빌드(`--ssl-revoke-best-effort` 등과 무관하게 SecureTransport 기반)를 쓰는 방법도 있습니다. 시스템 `/usr/bin/curl`은 키체인을 참조합니다.

3. **서버 쪽 문제(중간 인증서 누락)라면** 서버 관리자에게 fullchain 인증서(leaf + intermediate)를 설정하도록 요청하세요.

4. **임시 확인용으로만**: `curl -k https://...` (검증 비활성화). 중간자 공격에 노출되므로 토큰이나 민감한 데이터가 오가는 요청에는 쓰지 마세요. 스크립트나 CI에 넣는 것도 피하세요.

**참고**: Python, Node, Java 등 다른 도구도 각자 CA 번들을 쓰므로 같은 문제가 반복됩니다. 그때는 `REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` 같은 환경변수로 같은 사내 CA 파일을 지정하면 됩니다.

원하시면 `openssl s_client` 출력을 붙여 주세요. 어떤 경우인지 같이 확인해 드리겠습니다.