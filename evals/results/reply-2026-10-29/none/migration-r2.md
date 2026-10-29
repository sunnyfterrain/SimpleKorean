# Backfill이란?

기존 행들의 새 컬럼 값을 채워 넣는 작업입니다. NOT NULL 컬럼을 추가하려면 기존 모든 행에 값이 있어야 합니다. 그런데 20GB 테이블에 `ALTER TABLE ... ADD COLUMN ... NOT NULL`을 한 번에 실행하면 DB가 전체 행을 채우거나 검증하는 동안 테이블 락을 잡습니다. 이 때문에 마이그레이션이 멈춰 있고, 다른 쿼리까지 대기열에 쌓여 장애로 번질 수 있습니다.

DBA가 말한 방식은 NOT NULL 제약을 마지막에 거는 단계적 배포입니다.

## 우선 할 일

1. **멈춘 마이그레이션을 중단합니다.** 락 대기나 장시간 실행 중인 DDL이 다른 쿼리를 막고 있을 수 있습니다. 중단 전에 DBA와 상의하세요.
   - Postgres: `pg_stat_activity`에서 확인한 뒤 `pg_cancel_backend(pid)`
   - MySQL: `SHOW PROCESSLIST` 후 `KILL <id>`
2. **마이그레이션을 3단계로 나눕니다.**

## 단계별 절차

**1단계: nullable 컬럼 추가 (빠름)**
```sql
ALTER TABLE big_table ADD COLUMN new_col INT NULL;
-- 또는 상수 DEFAULT가 있으면 (PG 11+, MySQL 8 INSTANT) 메타데이터만 바뀌어 즉시 끝남
```

**2단계: 배포 코드가 새 컬럼에 값을 쓰도록 변경**
이후 들어오는 행은 값이 채워집니다.

**3단계: 기존 행을 배치로 backfill**
```sql
-- 예: 10,000건씩 반복, 배치 사이에 짧게 sleep
UPDATE big_table
SET new_col = <값 또는 계산식>
WHERE id BETWEEN :start AND :end AND new_col IS NULL;
```
- PK 범위로 나눠 작은 트랜잭션으로 커밋합니다.
- 복제 지연, 락 대기, 디스크/WAL 증가를 모니터링합니다.
- 트래픽이 적은 시간대에 돌리거나, 배치 크기와 sleep을 조절합니다.
- 재실행해도 안전하도록 `WHERE new_col IS NULL` 조건을 둡니다.

**4단계: NOT NULL 제약 적용**
- **Postgres:** 락을 최소화하려면 이렇게 합니다.
  ```sql
  ALTER TABLE big_table ADD CONSTRAINT new_col_nn CHECK (new_col IS NOT NULL) NOT VALID;
  ALTER TABLE big_table VALIDATE CONSTRAINT new_col_nn;  -- 쓰기를 막지 않음
  ALTER TABLE big_table ALTER COLUMN new_col SET NOT NULL; -- PG 12+는 검증된 CHECK가 있으면 스캔 생략
  ALTER TABLE big_table DROP CONSTRAINT new_col_nn;
  ```
- **MySQL:** `ALTER ... MODIFY new_col INT NOT NULL`을 `pt-online-schema-change`나 `gh-ost`로 실행하는 것이 안전합니다.

## 확인할 것
- DB 종류와 버전(Postgres, MySQL 등)
- 새 컬럼의 값이 상수인지, 다른 컬럼에서 계산되는지
- 서비스가 운영 중인지, 점검 시간대가 있는지

DB 종류와 기본값 규칙을 알려주시면 마이그레이션 파일과 backfill 스크립트를 구체적으로 작성해 드리겠습니다.