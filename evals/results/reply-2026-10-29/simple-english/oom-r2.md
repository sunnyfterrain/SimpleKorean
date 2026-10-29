Pod의 컨테이너가 memory limit(허용 메모리 상한)을 넘어서 리눅스 커널의 OOM killer가 프로세스를 강제 종료하고(exit code 137), kubelet이 재시작 정책에 따라 다시 띄우는 일이 반복되는 것입니다. 재시작이 계속되면 CrashLoopBackOff 상태로 바뀌고 재시작 간격도 점점 길어집니다.

먼저 원인이 어느 쪽인지 확인해야 합니다. 아래 명령으로 종료 이유와 현재 설정을 봅니다.

```
kubectl describe pod <pod> -n <ns>
kubectl top pod <pod> -n <ns> --containers
kubectl get pod <pod> -n <ns> -o jsonpath='{.spec.containers[*].resources}'
```

describe 출력의 Last State에 Reason: OOMKilled, Exit Code: 137이 보이면 컨테이너 메모리 초과가 맞습니다. 노드 전체 메모리가 부족해서 쫓겨난 경우는 Evicted로 표시되므로 다릅니다.

원인은 크게 세 가지입니다. 첫째, limit이 실제 사용량보다 낮게 잡힌 경우입니다. 이때는 `resources.limits.memory`를 올리고, `requests.memory`도 평소 사용량에 맞춰 함께 조정합니다. 둘째, 애플리케이션이 메모리 누수(leak)를 일으키는 경우입니다. 사용량이 시간에 따라 계속 증가하다가 죽는 패턴이면 limit을 올려도 시간만 늦출 뿐이므로, 힙 덤프나 프로파일러로 코드를 고쳐야 합니다. 셋째, 런타임이 컨테이너 limit을 모르는 경우입니다. 예를 들어 JVM은 `-XX:MaxRAMPercentage=70` 같은 옵션으로 힙을 limit의 일부로 제한하고, Node.js는 `--max-old-space-size`를 limit보다 작게 지정해야 합니다. 힙 외에 스레드 스택, 메타스페이스, 네이티브 버퍼도 메모리를 쓰므로 힙을 limit의 100%로 두면 안 됩니다.

수정 예시는 다음과 같습니다.

```yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"
```

limit은 관찰한 최대 사용량보다 20~30% 여유를 두는 것이 일반적입니다. 사용량 추이는 Prometheus의 `container_memory_working_set_bytes`로 확인할 수 있습니다. 이 값이 limit에 붙어 있으면 상한이 부족한 것이고, 계속 우상향하면 누수입니다.

원하시면 `kubectl describe` 출력이나 deployment YAML을 보내 주세요. 어느 경우인지 더 구체적으로 짚어 드리겠습니다.