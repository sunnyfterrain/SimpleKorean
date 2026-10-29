Backfill은 이미 있는 행들의 새 컬럼에 값을 채워 넣는 작업입니다. 지금 마이그레이션이 멈춘 이유는 NOT NULL 컬럼을 한 번에 추가하면서 20 GB 전체 행에 값을 쓰려 하기 때문이고, 그 동안 테이블 락(다른 쿼리를 막는 잠금)을 잡고 있을 가능성이 큽니다.

먼저 할 일은 멈춘 마이그레이션을 취소하는 것입니다. 이것이 테이블을 잡고 있으면 다른 서비스 쿼리까지 대기하므로, DBA와 함께 해당 세션을 종료하고 롤백이 끝났는지 확인하십시오.

그다음에는 작업을 세 단계로 나눕니다. 먼저 컬럼을 NULL 허용으로 추가합니다. 이 단계는 거의 즉시 끝납니다. 다음으로 기존 행을 1만 건에서 10만 건 정도씩 나눠서 값을 채웁니다. 마지막으로 모든 행에 값이 있는지 확인한 뒤 NOT NULL 제약을 겁니다. 코드에서는 배포 순서도 중요합니다. 새 행은 애플리케이션이 항상 값을 쓰도록 먼저 배포해야 backfill 도중에 NULL 행이 계속 생기지 않습니다.

PostgreSQL을 쓴다고 가정하면 다음과 같이 진행합니다. MySQL이라면 마지막 단계가 다르므로 DB 종류를 알려 주십시오.

```sql
ALTER TABLE big_table ADD COLUMN new_col integer;

-- 배치 반복 (id 범위를 바꿔 가며, 배치마다 커밋)
UPDATE big_table SET new_col = 0
WHERE id >= 1 AND id < 100001 AND new_col IS NULL;

ALTER TABLE big_table ADD CONSTRAINT new_col_nn CHECK (new_col IS NOT NULL) NOT VALID;
ALTER TABLE big_table VALIDATE CONSTRAINT new_col_nn;
ALTER TABLE big_table ALTER COLUMN new_col SET NOT NULL;
ALTER TABLE big_table DROP CONSTRAINT new_col_nn;
```

기본값이 상수이고 PostgreSQL 11 이상이면 `ADD COLUMN new_col integer NOT NULL DEFAULT 0`이 테이블을 다시 쓰지 않고 바로 끝나므로, 값이 단순한 상수라면 backfill 자체가 필요 없을 수 있습니다. 채울 값이 다른 컬럼에서 계산되는 경우에만 위의 배치 방식이 필요합니다.