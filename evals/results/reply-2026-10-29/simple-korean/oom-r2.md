Container의 메모리 사용량이 `resources.limits.memory`를 넘어서, 커널의 OOM killer가 프로세스를 SIGKILL로 종료하고 있습니다. kubelet은 종료된 container를 `restartPolicy`에 따라 다시 띄웁니다. 같은 이유로 계속 죽으면 CrashLoopBackOff로 보이고 재시작 간격이 점점 길어집니다.

먼저 원인을 확인하세요. 아래 명령에서 `Last State`가 `Reason: OOMKilled`, `Exit Code: 137`이면 limit 초과가 맞습니다.

```
kubectl describe pod <pod> -n <ns>
kubectl top pod <pod> -n <ns> --containers
```

`kubectl top`은 metrics-server가 설치되어 있어야 동작합니다. 죽기 직전의 사용량 추이는 Prometheus의 `container_memory_working_set_bytes`로 보는 편이 정확합니다.

원인은 대체로 세 가지입니다.

1. limit이 실제 필요량보다 낮습니다. 시작 직후부터 바로 죽는다면 이 경우입니다.
2. 메모리 누수가 있습니다. 사용량이 시간이 지나며 계속 오르다가 limit에서 죽습니다.
3. 런타임이 container limit을 모릅니다. JVM이나 Node.js의 heap이 limit보다 크게 잡히는 경우입니다. heap 외 영역(metaspace, thread stack, 네이티브 버퍼)도 limit에 포함되므로, heap만 limit에 맞춰도 죽을 수 있습니다.

바꿀 내용은 원인에 따라 다릅니다.

limit이 낮다면, 관측한 최대 사용량보다 20~30% 여유를 두고 올리세요.

```yaml
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "768Mi"
```

requests와 limits를 같게 두면 Guaranteed QoS가 되어 node 메모리가 부족할 때 eviction 순서에서 유리합니다.

JVM이면 heap 비율을 명시하세요. 예를 들어 `-XX:MaxRAMPercentage=70`을 쓰면 heap이 limit의 70%로 제한되고, 나머지는 heap 외 영역이 씁니다. Node.js는 `--max-old-space-size`를 limit의 75% 안팎으로 맞추세요.

누수가 의심되면 limit을 올려도 시간만 늦출 뿐입니다. heap dump나 profiler로 증가하는 객체를 찾아 코드를 고쳐야 합니다.

`describe`에 OOMKilled가 없는데 pod가 사라진다면, container limit이 아니라 node 전체의 메모리 부족일 수 있습니다. 이때는 `kubectl describe node`의 `MemoryPressure`와 eviction 이벤트를 확인하세요.

pod의 `describe` 출력이나 사용 중인 런타임(JVM, Node.js 등)을 알려 주시면 구체적인 값을 제안하겠습니다.