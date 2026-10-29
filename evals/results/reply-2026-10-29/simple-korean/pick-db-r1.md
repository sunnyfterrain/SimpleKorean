먼저 느린 쿼리를 찾아 `EXPLAIN (ANALYZE, BUFFERS)`로 실행 계획을 읽으세요. 4,000만 행은 Postgres 한 대가 충분히 감당하는 크기라서, sharding은 거의 마지막 수단입니다.

순서는 다음과 같이 권합니다.

1. `pg_stat_statements`를 켜고 총 실행 시간이 큰 쿼리 상위 10개를 뽑습니다. 느리다고 느끼는 쿼리와 실제 부하를 만드는 쿼리는 다른 경우가 많습니다.
2. 각 쿼리의 실행 계획에서 `Seq Scan`, 큰 `Rows Removed by Filter`, 디스크로 넘치는 sort를 확인합니다. 이런 항목이 보이면 대개 index 문제입니다.
3. index를 고칩니다. WHERE와 ORDER BY에 맞는 composite index, 일부 행만 조회할 때 쓰는 partial index, 테이블 접근을 없애는 covering index(`INCLUDE`)를 검토하세요. 쓰이지 않는 index는 쓰기만 느리게 하므로 `pg_stat_user_indexes`로 찾아 지웁니다.
4. 통계와 bloat(죽은 행이 쌓여 부푼 상태)를 점검합니다. `ANALYZE`가 오래 안 돌았거나 autovacuum이 밀려 있으면 planner가 잘못된 계획을 고릅니다.
5. 메모리 설정을 봅니다. `shared_buffers`, `effective_cache_size`, `work_mem`이 기본값에 가까우면 조정하세요. 자주 읽는 데이터가 메모리에 들어가는지도 `pg_statio_user_tables`의 cache hit 비율로 확인합니다.
6. 쿼리를 고칩니다. 큰 `OFFSET` 페이지네이션은 keyset 방식으로 바꾸고, `SELECT *`는 필요한 컬럼만 고르며, N+1 호출은 한 번에 묶으세요.

여기까지 하고도 느리면 다음 단계로 갑니다. 읽기 부하가 문제라면 read replica나 캐시(Redis 등)를 먼저 붙이세요. 오래된 데이터를 거의 안 읽는 시계열 성격이면 날짜 기준 partitioning이 맞습니다. partitioning은 한 서버 안에서 테이블을 나누는 것이라 sharding보다 훨씬 단순합니다.

sharding은 복잡도가 큽니다. 서버 간 JOIN과 transaction이 어려워지고, resharding과 운영 부담이 생깁니다. 단일 서버의 쓰기 한계나 저장 용량 한계에 실제로 닿았을 때 검토해도 늦지 않습니다.

느린 쿼리와 실행 계획을 알려 주시면 어떤 단계가 효과적일지 구체적으로 짚어 드리겠습니다.