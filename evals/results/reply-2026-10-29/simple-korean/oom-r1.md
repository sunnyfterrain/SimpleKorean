Container의 메모리 사용량이 `resources.limits.memory`를 넘어서, 커널의 OOM killer가 프로세스를 SIGKILL로 종료하고 있습니다. kubelet은 종료된 container를 `restartPolicy`에 따라 다시 띄웁니다. 같은 이유로 계속 죽으면 재시작 간격이 늘어나며 CrashLoopBackOff로 보입니다.

먼저 원인이 limit 초과인지 확인하세요.

```
kubectl describe pod <pod> | grep -A6 "Last State"
```

`Reason: OOMKilled`와 `Exit Code: 137`이 나오면 container가 자기 limit에 걸린 것입니다. Node 전체의 메모리가 부족해서 pod가 쫓겨나는 경우는 `Evicted`로 표시되므로 구분됩니다.

그다음 실제 사용량을 보세요.

```
kubectl top pod <pod> --containers
```

재시작 직전의 최대 사용량이 limit에 가까우면 limit이 너무 낮은 것입니다. 시간이 지날수록 사용량이 계속 오르면 memory leak입니다. Prometheus가 있으면 `container_memory_working_set_bytes`를 그래프로 확인하세요. 이 값이 OOM killer가 보는 기준에 가장 가깝습니다.

원인별 조치는 다음과 같습니다.

1. limit이 낮은 경우: 관측된 최대 사용량의 1.2배에서 1.5배로 `limits.memory`를 올리고, `requests.memory`는 평상시 사용량에 맞추세요.
2. 런타임이 limit을 모르는 경우: JVM은 `-XX:MaxRAMPercentage=75`를 지정하세요. Node.js는 `--max-old-space-size`를 limit보다 작게 설정하세요. heap 외에 metaspace, thread stack, native 메모리도 limit에 포함됩니다.
3. 메모리 기반 volume을 쓰는 경우: `emptyDir`에 `medium: Memory`를 쓰거나 `/dev/shm`에 파일을 쌓으면 그 크기가 container 메모리로 계산됩니다.
4. Leak인 경우: limit을 올려도 재시작 주기만 늘어납니다. heap dump나 profiler로 원인 코드를 찾아 고치세요.
5. 부하에 따라 사용량이 크게 변하는 경우: replica를 늘려 요청을 나누거나, VPA(Vertical Pod Autoscaler)로 limit을 자동 조정하세요.

Deployment 이름, 런타임, `describe` 출력과 `kubectl top` 결과를 알려주시면 어느 경우인지 더 좁혀서 말씀드리겠습니다.