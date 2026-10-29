backfill은 이미 있는 행들의 새 컬럼에 값을 채워 넣는 작업이고, 20 GB 테이블에서는 한 번에 처리하지 않고 나눠서 해야 합니다. 마이그레이션이 멈춘 이유는 아마 `ADD COLUMN ... NOT NULL`이 기존 모든 행을 검사하거나 다시 쓰면서 테이블 전체에 락(다른 쿼리를 막는 잠금)을 잡고 있기 때문입니다. 이 상태가 길어지면 그 테이블을 읽고 쓰는 다른 요청도 줄줄이 대기합니다.

먼저 DBA와 함께 멈춘 마이그레이션 세션을 취소하세요. 취소하면 트랜잭션이 롤백되어 컬럼은 추가되지 않은 상태로 돌아갑니다. 락 때문에 서비스가 막히고 있다면 이 작업을 먼저 하는 것이 좋습니다. 단, 세션을 종료하기 전에 DBA에게 확인받으세요.

그다음 변경을 세 단계로 나눕니다. 1단계에서는 NOT NULL 없이 컬럼만 추가합니다. 이 작업은 대부분 바로 끝납니다. 그리고 새 행에는 애플리케이션이 값을 쓰도록 코드를 배포합니다. 2단계에서는 기존 행을 기본키 범위로 1만 건 정도씩 나눠 채우고, 배치 사이에 잠깐 쉽니다. 3단계에서는 모든 행에 값이 있는 것을 확인한 뒤 NOT NULL 제약을 겁니다.

PostgreSQL을 쓰신다면 아래처럼 하면 3단계도 긴 락 없이 끝납니다.

```sql
ALTER TABLE t ADD COLUMN c integer;

-- 배치 반복 (id 범위를 바꿔 가며 실행)
UPDATE t SET c = 0 WHERE id >= 1 AND id < 10001 AND c IS NULL;

ALTER TABLE t ADD CONSTRAINT c_nn CHECK (c IS NOT NULL) NOT VALID;
ALTER TABLE t VALIDATE CONSTRAINT c_nn;
ALTER TABLE t ALTER COLUMN c SET NOT NULL;  -- PG 12 이상은 전체 스캔을 건너뜀
ALTER TABLE t DROP CONSTRAINT c_nn;
```

MySQL이라면 같은 흐름이지만 마지막 변경에 `gh-ost`나 `pt-online-schema-change` 같은 온라인 스키마 변경 도구를 쓰는 것이 안전합니다.

DB 종류와 버전, 그리고 채울 값이 고정값인지 다른 컬럼에서 계산되는 값인지 알려 주시면 배치 쿼리를 더 구체적으로 써 드리겠습니다.