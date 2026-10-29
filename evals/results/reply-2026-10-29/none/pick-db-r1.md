Sharding은 마지막 수단입니다. 4,000만 행은 Postgres에게 큰 규모가 아닙니다. 보통 단일 노드에서 수억~수십억 행까지 처리합니다. 느린 원인을 먼저 찾으세요.

## 1. 느린 쿼리를 측정합니다
- `pg_stat_statements`로 총 시간 기준 상위 쿼리를 찾습니다.
- 느린 쿼리에 `EXPLAIN (ANALYZE, BUFFERS)`를 실행합니다.
- 확인할 것은 Seq Scan 여부, 실제 행 수와 추정 행 수의 차이, `shared read`(디스크)와 `shared hit`(캐시)의 비율입니다.

## 2. 인덱스를 점검합니다
- WHERE, JOIN, ORDER BY 컬럼에 맞는 복합 인덱스가 있는지 봅니다. 컬럼 순서도 중요합니다.
- 조회 대상이 일부 행뿐이면 partial index를 씁니다. 예: `WHERE status = 'active'`.
- 인덱스만으로 답이 나오게 `INCLUDE`를 쓰는 covering index도 고려합니다.
- 안 쓰는 인덱스와 중복 인덱스는 지웁니다. 쓰기 성능과 캐시 효율에 영향을 줍니다.
- 운영 중에는 `CREATE INDEX CONCURRENTLY`를 씁니다.

## 3. 통계와 bloat을 확인합니다
- `ANALYZE`를 실행합니다. 통계가 오래되면 플래너가 잘못된 계획을 고릅니다.
- `pg_stat_user_tables`에서 dead tuple 비율과 autovacuum 동작을 봅니다.
- bloat이 심하면 `pg_repack`을 검토합니다.
- 필요하면 `ALTER TABLE ... SET (autovacuum_vacuum_scale_factor = 0.02)`처럼 이 테이블의 autovacuum 설정을 조정합니다.

## 4. 쿼리 패턴을 개선합니다
- `SELECT *`를 줄이고 필요한 컬럼만 가져옵니다.
- 큰 `OFFSET` 대신 keyset pagination을 씁니다.
- N+1 쿼리와 불필요한 `COUNT(*)`를 제거합니다. 근사치로 충분하면 통계 기반 추정값을 씁니다.
- 컬럼에 함수를 씌워 인덱스를 못 타는 조건이 없는지 봅니다.

## 5. 설정과 하드웨어를 확인합니다
- `shared_buffers`, `effective_cache_size`, `work_mem`, `random_page_cost`(SSD면 1.1 정도)를 봅니다.
- 자주 읽는 데이터(working set)가 RAM에 들어가는지 확인합니다. 안 들어가면 메모리 증설이 가장 싼 해결책일 수 있습니다.

## 6. 그래도 부족하면 sharding 전에 이것들을 씁니다
- **Read replica**: 읽기가 병목이면 읽기를 분산합니다.
- **캐싱**: Redis 등으로 반복 조회를 줄입니다.
- **파티셔닝**: 시간이나 키 기준 declarative partitioning입니다. partition pruning이 되려면 쿼리에 파티션 키가 있어야 합니다. 오래된 데이터 보관과 삭제에도 유리합니다.
- **Materialized view / 집계 테이블**: 무거운 집계를 미리 계산해 둡니다.
- **Scale up**: CPU, RAM, IOPS를 올립니다.

## Sharding을 검토할 시점
위 단계를 거치고도 아래 중 하나라도 해당할 때입니다.
- 쓰기 처리량이 단일 primary의 한계를 넘습니다.
- 데이터가 단일 노드 용량을 넘습니다.
- 테넌트나 지역별 데이터 분리가 필요합니다.

Sharding은 cross-shard 조인과 트랜잭션, 리밸런싱, 운영 복잡도를 크게 늘립니다. 되돌리기도 어렵습니다.

## 제안
`EXPLAIN (ANALYZE, BUFFERS)` 결과와 느린 쿼리 몇 개, 테이블 스키마를 공유해 주시면 원인을 같이 분석해 드리겠습니다. 대부분은 인덱스나 쿼리 수정만으로 해결됩니다.