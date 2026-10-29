# OOMKilled 재시작 원인과 해결 방법

## 무슨 일이 일어나는가

컨테이너의 메모리 사용량이 `resources.limits.memory`를 넘으면 리눅스 커널의 cgroup OOM killer가 프로세스를 SIGKILL(종료 코드 **137**)로 죽입니다. kubelet은 이를 `OOMKilled`로 기록하고, `restartPolicy: Always`에 따라 컨테이너를 다시 띄웁니다. 재시작 후에도 같은 원인이 반복되면 `CrashLoopBackOff`로 넘어가고 재시작 간격이 최대 5분까지 늘어납니다.

참고로 이것은 **노드 전체**의 메모리 부족(Node pressure eviction)과는 다릅니다. OOMKilled는 해당 컨테이너가 자기 limit을 넘은 경우입니다.

## 먼저 확인할 것

```bash
# 마지막 종료 사유 확인 (Reason: OOMKilled, Exit Code: 137)
kubectl describe pod <pod> | grep -A8 "Last State"

# 현재 메모리 사용량 (metrics-server 필요)
kubectl top pod <pod> --containers

# 직전 컨테이너의 로그
kubectl logs <pod> --previous

# 설정된 limit/request
kubectl get pod <pod> -o jsonpath='{.spec.containers[*].resources}'
```

Prometheus를 쓴다면 `container_memory_working_set_bytes`를 limit과 비교해 보면 증가 패턴(점진적 증가 vs 시작 직후 급등)을 볼 수 있습니다.

## 원인별 판단

| 증상 | 가능성 높은 원인 | 조치 |
|---|---|---|
| 시작 직후 바로 죽음 | limit이 너무 낮음, 기동 시 대량 로딩 | limit 상향 |
| 시간이 지나며 서서히 증가 후 죽음 | 메모리 누수, 캐시/큐 무한 증가 | 애플리케이션 수정, 프로파일링 |
| 특정 요청/배치 때 급등 | 큰 페이로드, 동시성 과다 | 동시성/배치 크기 제한, limit 상향 |
| JVM/Node 등 런타임 앱 | 힙 설정이 컨테이너 limit을 고려하지 않음 | 런타임 메모리 옵션 조정 |
| 파일 I/O나 `emptyDir(medium: Memory)` 사용 | 페이지 캐시/tmpfs가 limit에 포함됨 | tmpfs 크기 제한, 디스크 볼륨 사용 |

## 무엇을 바꿔야 하는가

**1. limit과 request를 실제 사용량에 맞춘다**

```yaml
resources:
  requests:
    memory: "512Mi"   # 평소 사용량 + 여유
  limits:
    memory: "1Gi"     # 피크 사용량 + 20~30% 여유
```

메모리는 CPU와 달리 압축할 수 없어서 throttle되지 않고 바로 kill됩니다. 그래서 request와 limit을 같거나 가깝게 두는 편이 안정적입니다(Guaranteed QoS).

**2. 런타임이 limit을 인식하게 한다**

- **JVM**: `-XX:MaxRAMPercentage=75.0` (힙 외에 메타스페이스, 스레드 스택, 다이렉트 버퍼가 추가로 필요하므로 100%로 두면 안 됩니다)
- **Node.js**: `--max-old-space-size`를 limit의 약 75% 수준으로 지정
- **Go**: `GOMEMLIMIT`를 limit의 90% 정도로 설정
- **Python**: 누수 의심 시 `tracemalloc`이나 `memray`로 확인

**3. 근본 원인이 누수라면** limit을 올리는 것은 재시작 주기를 늦출 뿐입니다. 힙 덤프나 프로파일러로 증가하는 객체를 찾아 고쳐야 합니다.

**4. 보조 수단**

- HPA로 부하를 분산해 pod당 메모리 부담을 줄입니다.
- VPA를 recommendation 모드로 돌려 적정 값을 확인합니다.

## 다음 단계

원인을 더 좁혀 드리려면 아래 정보가 필요합니다.

- `kubectl describe pod` 출력의 `Last State`, `Limits`, `Requests` 부분
- 애플리케이션 언어/런타임 (JVM, Node, Python 등)
- 재시작이 시작 직후인지, 일정 시간 후인지

이 내용을 알려주시면 구체적인 값을 제안해 드리겠습니다.