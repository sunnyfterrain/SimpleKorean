## backfill이란?

backfill은 **기존 행들의 새 컬럼에 값을 채워 넣는 작업**입니다. `NOT NULL` 컬럼은 모든 행에 값이 있어야 합니다. 그래서 DB는 20GB 전체 행에 값을 채우거나 검증해야 하고, 그동안 테이블 락을 잡습니다. 이 때문에 마이그레이션이 멈춰 보입니다. 이 작업을 한 번에 하지 말고 작은 배치로 나눠서 하라는 것이 DBA의 요청입니다.

## 지금 할 일

1. **멈춘 마이그레이션을 먼저 취소하세요.** 멈춘 `ALTER`가 락을 잡거나 락 대기열에서 다른 쿼리를 막아 서비스 장애로 번질 수 있습니다. 취소는 DBA에게 요청하거나, 직접 한다면 `pg_cancel_backend`나 `KILL`을 쓰세요.
2. **마이그레이션을 3단계로 나누세요.** (PostgreSQL 기준입니다.)

   ```sql
   -- 1단계: nullable로 추가 (메타데이터만 변경, 즉시 끝남)
   SET lock_timeout = '3s';
   ALTER TABLE big_table ADD COLUMN new_col integer;
   -- 상수 기본값이 필요하면 PG11+에서는 DEFAULT를 붙여도 즉시 끝남
   ```

   ```sql
   -- 2단계: 배치 backfill (애플리케이션/스크립트에서 반복 실행)
   UPDATE big_table
   SET new_col = <값>
   WHERE id > :last_id AND id <= :last_id + 10000
     AND new_col IS NULL;
   -- 배치마다 커밋하고 sleep을 줘서 복제 지연과 락 경합을 줄이세요.
   ```

   ```sql
   -- 3단계: NOT NULL 적용 (스캔은 하되 락 부담이 작은 방식)
   ALTER TABLE big_table ADD CONSTRAINT new_col_nn
     CHECK (new_col IS NOT NULL) NOT VALID;
   ALTER TABLE big_table VALIDATE CONSTRAINT new_col_nn;  -- 쓰기를 막지 않음
   ALTER TABLE big_table ALTER COLUMN new_col SET NOT NULL; -- PG12+, 검증된 CHECK를 이용해 스캔 생략
   ALTER TABLE big_table DROP CONSTRAINT new_col_nn;
   ```

3. **새로 들어오는 행도 챙기세요.** backfill 중에 들어오는 행이 NULL이 되지 않도록, 1단계 직후 애플리케이션이 새 컬럼에 값을 쓰게 배포하거나 `DEFAULT`를 설정하세요. 그렇게 하면 backfill은 기존 행만 처리하면 됩니다.

## 주의할 점

- 모든 `ALTER` 앞에 `lock_timeout`을 걸어 두세요. 락을 못 잡으면 실패하게 해서 서비스를 막지 않기 위해서입니다.
- 한 트랜잭션으로 20GB 전체를 `UPDATE`하지 마세요. 락과 WAL이 커지고 bloat가 생기며 복제 지연도 발생합니다. 배치 크기는 보통 1천~1만 행으로 시작해 부하를 보며 조정하세요.
- backfill 뒤에는 `VACUUM`이 필요할 수 있습니다. DBA와 상의하세요.
- MySQL이라면 방식이 다릅니다. `gh-ost`나 `pt-online-schema-change` 같은 온라인 스키마 변경 도구를 쓰는 것이 일반적입니다.

DB 종류와 버전(PostgreSQL 몇 버전인지, MySQL인지), 채울 값이 상수인지 다른 컬럼에서 계산하는지 알려주시면 구체적인 스크립트를 작성해 드릴 수 있습니다. 사용 중인 마이그레이션 도구(Rails, Django, Flyway 등)도 알려주세요.