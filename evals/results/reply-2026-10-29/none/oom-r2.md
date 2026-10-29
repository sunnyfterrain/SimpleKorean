# OOMKilled 원인과 해결 방법

## 무슨 일이 일어나는가

컨테이너의 메모리 사용량이 `resources.limits.memory`를 초과하면 리눅스 커널의 cgroup OOM killer가 프로세스를 SIGKILL(exit code 137)로 종료합니다. kubelet은 이를 `OOMKilled`로 기록하고 `restartPolicy`에 따라 컨테이너를 다시 시작합니다. 같은 이유로 반복해서 죽으면 `CrashLoopBackOff`로 바뀌고 재시작 간격이 점점 길어집니다(최대 5분).

참고로 노드 전체 메모리가 부족해서 죽는 경우도 있지만, 대부분은 **컨테이너 자체의 limit 초과**입니다.

## 흔한 원인

1. **limit이 너무 낮음**: 실제 정상 사용량보다 작게 설정됨
2. **메모리 누수**: 시간이 지나며 계속 증가 (재시작 주기가 일정하면 의심)
3. **런타임 설정 불일치**
   - JVM: 힙(`-Xmx`)만 보면 안 되고 metaspace, 스레드 스택, 네이티브 메모리가 추가됨. 힙을 limit의 약 50~75%로 제한해야 함 (`-XX:MaxRAMPercentage=70` 등)
   - Node.js: `--max-old-space-size`가 limit보다 크면 GC 전에 죽음
   - Go: `GOMEMLIMIT` 미설정
4. **순간적인 피크**: 시작 시점의 캐시 로딩, 대용량 요청 처리, 배치 작업
5. **tmpfs/emptyDir(medium: Memory)**나 페이지 캐시도 컨테이너 메모리로 계산됨
6. **사이드카**(istio-proxy 등)가 OOM되는 경우 — 어느 컨테이너인지 확인 필요

## 진단 순서

```bash
# 1. 어느 컨테이너가, 어떤 사유로 죽었는지
kubectl describe pod <pod> -n <ns>
#   → Last State: Terminated, Reason: OOMKilled, Exit Code: 137 확인

# 2. 현재 사용량 vs limit
kubectl top pod <pod> --containers -n <ns>

# 3. 직전 컨테이너 로그
kubectl logs <pod> -c <container> --previous -n <ns>

# 4. 현재 설정된 requests/limits
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].resources}'

# 5. 노드 레벨 OOM 여부
kubectl describe node <node> | grep -i -A5 "oom\|MemoryPressure"
```

Prometheus가 있다면 `container_memory_working_set_bytes`의 추이를 보세요. 완만히 우상향하면 누수, 시작 직후 급등하면 피크 문제, 일정 수준에서 평평하다가 죽으면 limit 부족입니다.

## 무엇을 바꿔야 하는가

**1) limit/request 조정 (가장 빠른 조치)**

```yaml
resources:
  requests:
    memory: "512Mi"   # 평균 사용량 기준
  limits:
    memory: "1Gi"     # 관측된 피크 + 20~30% 여유
```

- 메모리는 압축 불가능한 자원이라 **requests = limits**로 두면 Guaranteed QoS가 되어 노드 압박 시 가장 늦게 쫓겨납니다.
- 단순히 limit만 올리면 누수는 해결되지 않고 죽는 시점만 늦춰집니다.

**2) 런타임을 컨테이너 한도에 맞추기** (위 3번 항목 참고)

**3) 누수라면 애플리케이션 수정**
힙 덤프/프로파일링(JVM은 `jmap`/async-profiler, Go는 pprof, Node는 `--heapsnapshot-signal`)으로 원인을 찾으세요.

**4) 보조 수단**
- 부하가 원인이면 HPA로 pod당 메모리 부담 분산
- VPA(추천 모드)로 적정 값 산정
- 시작 피크가 문제면 캐시 워밍/배치 크기 조절

## 다음 단계

원인을 정확히 짚으려면 아래 정보가 필요합니다. 공유해 주시면 구체적인 값을 제안드리겠습니다.

- `kubectl describe pod` 결과의 `Last State` 부분과 현재 `resources`
- 사용 언어/런타임 (JVM, Node, Go 등)
- 재시작 패턴 (시작 직후 vs 몇 시간 후)
- `kubectl top pod --containers` 결과