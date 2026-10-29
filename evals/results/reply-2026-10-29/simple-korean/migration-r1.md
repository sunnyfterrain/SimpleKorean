backfill은 이미 있는 행의 새 컬럼에 값을 채우는 작업입니다. 마이그레이션 한 번에 컬럼 추가, 값 채우기, NOT NULL 설정을 모두 하지 말고, 세 단계로 나눠 실행하라는 뜻입니다.

멈춘 이유는 20 GB 테이블 전체를 한 트랜잭션에서 처리하기 때문으로 보입니다. NOT NULL 제약은 모든 행에 값이 있어야 걸립니다. 그래서 DB가 전체 행을 쓰거나 검사하는 동안 테이블 lock을 잡고, 그 사이 다른 쿼리가 모두 대기합니다. 엔진과 버전에 따라 다르지만, 이 상태가 오래 가면 서비스 장애로 이어집니다.

다음 순서로 진행하세요.

1. 멈춘 마이그레이션을 취소합니다. Postgres라면 `pg_stat_activity`에서 해당 세션을 찾아 `pg_cancel_backend`를 실행하세요. 이후 `pg_locks`에 대기 중인 세션이 남았는지 확인하세요.
2. NOT NULL 없이 컬럼만 추가합니다. default 없는 nullable 컬럼 추가는 metadata만 바꾸므로 거의 즉시 끝납니다.
3. 애플리케이션이 새 행에 이 컬럼 값을 쓰도록 먼저 배포합니다. 그래야 backfill 중에 NULL인 행이 새로 생기지 않습니다.
4. 기존 행을 batch로 채웁니다. 기본 키 범위로 5,000~10,000행씩 `UPDATE`하고, batch마다 commit하세요. batch 사이에 짧게 쉬면 replica 지연과 lock 경합이 줄어듭니다.
5. NULL이 남았는지 확인한 뒤 NOT NULL을 겁니다. Postgres에서는 `CHECK (col IS NOT NULL) NOT VALID`를 추가하고 `VALIDATE CONSTRAINT`를 실행하세요. 그다음 `SET NOT NULL`을 실행하고 CHECK 제약을 지우세요. 이 방식은 전체 테이블 lock 없이 검증합니다.

MySQL이면 5번 대신 `gh-ost`나 `pt-online-schema-change`를 쓰는 편이 안전합니다.

DB 엔진과 버전을 알려 주시면 해당 엔진에 맞는 SQL과 batch 스크립트를 작성해 드리겠습니다. DBA에게는 backfill 시간대와 batch 크기 기준도 확인해 두세요.