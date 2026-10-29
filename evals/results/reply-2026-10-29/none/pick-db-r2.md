4,000만 행은 Postgres 기준으로 큰 편이 아니라서, sharding은 거의 마지막 선택지입니다. 먼저 이 순서로 확인해 보세요.

## 1. 왜 느린지 측정하기
- **`EXPLAIN (ANALYZE, BUFFERS)`**로 느린 쿼리의 실제 실행 계획을 봅니다. Seq Scan인지, 인덱스를 타는지, 디스크 읽기(`read`)가 많은지 확인합니다.
- **`pg_stat_statements`**로 총 소요 시간 기준 상위 쿼리를 찾습니다. 느린 쿼리 하나가 아니라 호출 빈도가 높은 쿼리가 원인인 경우가 많습니다.
- 병목이 CPU, I/O, 락, 커넥션 중 어디인지 모니터링으로 확인합니다.

## 2. 인덱스와 쿼리 점검
- WHERE, JOIN, ORDER BY 컬럼에 맞는 **복합 인덱스**가 있는지 봅니다. 컬럼 순서도 중요합니다.
- **부분 인덱스**(`WHERE status = 'active'`)나 **커버링 인덱스**(`INCLUDE`)로 Index Only Scan을 유도합니다.
- `OFFSET` 페이징은 keyset(커서) 페이징으로 바꿉니다.
- `SELECT *`를 피하고, 함수가 걸린 컬럼(`WHERE lower(col)=...`)에는 표현식 인덱스를 만듭니다.
- `ANALYZE`로 통계를 갱신하고, 플래너가 엉뚱한 계획을 고르면 `default_statistics_target`을 조정합니다.

## 3. 테이블 상태와 설정
- **Bloat**: UPDATE/DELETE가 많으면 dead tuple이 쌓입니다. autovacuum 설정을 점검하고, 심하면 `pg_repack`을 씁니다.
- **메모리**: `shared_buffers`(RAM의 약 25%), `effective_cache_size`, `work_mem`을 확인합니다. 작업 집합(working set)이 메모리에 들어가는지가 핵심입니다.
- `random_page_cost`가 SSD 환경에 맞게(1.1 정도) 설정돼 있는지 봅니다.

## 4. 구조적 해결 (필요할 때만)
- **Read replica**: 읽기 부하가 문제라면 가장 간단하고 효과가 큽니다. 복제 지연은 감수해야 합니다.
- **캐싱**: Redis 등으로 핫 데이터를 캐시합니다.
- **파티셔닝**(declarative partitioning): 시간이나 테넌트 기준으로 쿼리가 자연스럽게 파티션 하나만 건드리면 효과가 큽니다. 단일 DB 안에서 해결되므로 sharding보다 훨씬 간단합니다.
- 오래된 데이터는 아카이빙하거나, 집계 쿼리는 materialized view나 요약 테이블로 분리합니다.
- 하드웨어 스케일업(RAM, NVMe)도 비용 대비 효과가 좋은 경우가 많습니다.

## 5. Sharding은 언제?
단일 노드의 쓰기 처리량 한계, 수 TB 이상의 데이터, 위 방법을 다 써도 해결되지 않는 상황일 때입니다. 그때도 Citus 같은 도구를 먼저 검토하세요. Sharding을 하면 크로스 샤드 조인과 트랜잭션, 리밸런싱, 운영 복잡도가 크게 늘어납니다.

---

느린 쿼리 하나와 그 `EXPLAIN (ANALYZE, BUFFERS)` 결과, 테이블 스키마를 공유해 주시면 구체적으로 어떤 인덱스나 설정을 바꿀지 같이 볼 수 있습니다.