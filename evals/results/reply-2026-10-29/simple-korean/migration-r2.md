Backfill은 기존 행에 새 컬럼의 값을 채우는 작업입니다. NOT NULL 컬럼은 모든 행에 값이 있어야 하므로, 20 GB 테이블 전체를 한 번에 고치는 ALTER는 오래 걸리고 그동안 테이블을 잠급니다. 지금 멈춘 것처럼 보이는 이유가 이것입니다. 아래는 PostgreSQL 기준입니다. MySQL이면 알려 주세요.

먼저 멈춘 마이그레이션을 취소하세요. 잠금을 쥔 채로 두면 다른 쿼리가 모두 대기합니다. 트랜잭션이 롤백되는 동안은 시간이 걸릴 수 있습니다.

```sql
SELECT pid, state, wait_event_type, query
FROM pg_stat_activity
WHERE query ILIKE '%ALTER TABLE%';

SELECT pg_cancel_backend(<pid>);
```

그다음 세 단계로 나눠서 다시 적용하세요.

1. 컬럼을 NULL 허용으로 추가합니다. 기본값이 없으면 metadata만 바뀌므로 즉시 끝납니다. 이때 앱 코드가 새 행에 값을 쓰도록 먼저 배포하세요.

```sql
ALTER TABLE t ADD COLUMN new_col integer;
```

2. 기존 행을 배치로 backfill합니다. 한 번에 1만 행 안팎으로 나누고, 배치마다 commit하세요. 배치 사이에 짧게 쉬면 replica 지연과 lock 경합을 줄일 수 있습니다.

```sql
UPDATE t SET new_col = <값>
WHERE id IN (
  SELECT id FROM t WHERE new_col IS NULL ORDER BY id LIMIT 10000
);
```

NULL 행이 없을 때까지 반복합니다. 스크립트나 별도 migration job으로 돌리는 것이 안전합니다.

3. NOT NULL을 안전하게 겁니다. CHECK 제약을 먼저 NOT VALID로 추가하고 따로 검증하면, 긴 잠금 없이 끝낼 수 있습니다. PostgreSQL 12 이상에서는 검증된 CHECK가 있으면 SET NOT NULL이 전체 scan을 건너뜁니다.

```sql
ALTER TABLE t ADD CONSTRAINT new_col_nn CHECK (new_col IS NOT NULL) NOT VALID;
ALTER TABLE t VALIDATE CONSTRAINT new_col_nn;
ALTER TABLE t ALTER COLUMN new_col SET NOT NULL;
ALTER TABLE t DROP CONSTRAINT new_col_nn;
```

모든 행에 같은 상수를 넣는 경우라면 더 간단합니다. PostgreSQL 11 이상에서는 `ADD COLUMN new_col integer NOT NULL DEFAULT 0`이 테이블을 다시 쓰지 않고 즉시 끝납니다. 값이 행마다 달라야 할 때만 위 절차가 필요합니다.

DBA에게 backfill 배치 크기와 실행 시간대를 확인받는 것도 권합니다.