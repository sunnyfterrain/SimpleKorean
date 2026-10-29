Pod의 컨테이너가 설정된 메모리 limit보다 많은 메모리를 쓰려고 해서, 리눅스 커널이 그 프로세스를 강제 종료(SIGKILL, exit code 137)하고 있습니다. kubelet은 컨테이너가 죽었으니 restartPolicy에 따라 다시 띄우고, 같은 일이 반복되면 CrashLoopBackOff 상태가 됩니다.

먼저 원인이 어느 쪽인지 확인해야 합니다. 아래 명령으로 마지막 종료 사유와 현재 limit을 봅니다.

```
kubectl describe pod <pod> -n <namespace>
kubectl top pod <pod> -n <namespace> --containers
```

describe 출력의 Last State에 Reason: OOMKilled와 Exit Code: 137이 보이면 컨테이너 limit 초과가 맞습니다. 노드 전체의 메모리가 부족해서 죽은 경우에는 Pod가 eviction(노드가 Pod를 쫓아내는 것)되며 사유가 다르게 표시됩니다.

원인은 크게 세 가지입니다. 첫째, limit이 실제 필요량보다 작게 잡혀 있는 경우입니다. 둘째, 애플리케이션에 메모리 누수가 있거나 트래픽, 캐시, 큰 요청 때문에 사용량이 계속 늘어나는 경우입니다. 셋째, JVM이나 Node.js 같은 런타임이 컨테이너 limit이 아니라 노드 전체 메모리를 기준으로 힙 크기를 잡는 경우입니다. 이때는 힙이 limit보다 커져서 바로 죽습니다.

바꿀 내용은 원인에 따라 다릅니다. limit이 작은 경우에는 Deployment의 resources를 올립니다. 이때 requests와 limits를 같은 값으로 두면 메모리 동작이 예측 가능해집니다.

```
resources:
  requests:
    memory: "512Mi"
  limits:
    memory: "1Gi"
```

값은 추측하지 말고, kubectl top이나 Prometheus의 container_memory_working_set_bytes 그래프에서 피크 사용량을 보고 그보다 20~30% 여유 있게 정하십시오. 런타임이 원인이면 힙을 limit보다 낮게 제한합니다. JVM은 `-XX:MaxRAMPercentage=75`, Node.js는 `--max-old-space-size`를 쓰면 됩니다. limit을 올려도 사용량이 계속 우상향하면 누수입니다. 이 경우 limit을 키우는 것은 재시작 주기를 늦출 뿐이므로, 힙 덤프나 프로파일러로 코드를 고쳐야 합니다.

원인을 좁히려면 Deployment YAML, 사용 중인 언어와 런타임, kubectl top 결과를 알려 주십시오. 그러면 구체적인 값을 제안하겠습니다.