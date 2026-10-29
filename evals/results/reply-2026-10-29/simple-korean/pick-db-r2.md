4,000만 행은 Postgres 한 대로 충분히 빠르게 다룰 수 있는 규모이므로, sharding보다 먼저 느린 원인을 찾으세요.

다음 순서로 진행하는 것을 권합니다.

1. `pg_stat_statements`로 실제로 느린 쿼리를 찾습니다. 총 소요 시간이 큰 쿼리부터 봅니다.
2. 해당 쿼리에 `EXPLAIN (ANALYZE, BUFFERS)`를 실행합니다. Seq Scan, 큰 Sort, 예상 행 수와 실제 행 수의 차이를 확인합니다.
3. 인덱스를 점검합니다. WHERE와 ORDER BY 조건에 맞는 복합 인덱스, 일부 행만 쓰는 쿼리용 partial index, 테이블 접근을 피하는 `INCLUDE` 컬럼 인덱스를 검토합니다.
4. 통계와 bloat를 확인합니다. `ANALYZE`를 실행하고, `pg_stat_user_tables`에서 dead tuple 비율과 autovacuum 동작을 봅니다.
5. 메모리 설정을 봅니다. `shared_buffers`, `effective_cache_size`, `work_mem`이 기본값이면 조정하세요. 자주 읽는 데이터가 메모리에 들어가는지도 확인합니다.
6. 애플리케이션 쪽을 봅니다. N+1 쿼리, 불필요한 `SELECT *`, 깊은 OFFSET 페이징(keyset 페이징으로 대체)이 흔한 원인입니다.

이 단계를 거쳐도 느리면 다음 수단을 순서대로 고려하세요. 시간이나 tenant 기준으로 자르는 파티셔닝(partitioning), 읽기 부하를 나누는 read replica, 반복 조회용 캐시입니다. 이 정도는 sharding보다 운영 부담이 훨씬 작습니다.

sharding은 쓰기 처리량이나 데이터 크기가 단일 서버의 한계(대략 수 TB, 수십억 행 이상)에 닿았을 때 검토합니다. 지금 단계에서 도입하면 cross-shard JOIN, 트랜잭션, 재분배 문제를 떠안게 됩니다.

느린 쿼리와 `EXPLAIN ANALYZE` 결과를 공유해 주시면 구체적인 원인을 같이 볼 수 있습니다.