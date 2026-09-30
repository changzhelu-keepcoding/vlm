# 学习记录

每次学习只记录一次可复现的实验。建议复制下面模板追加到文档末尾。

## 记录模板

### 日期：YYYY-MM-DD

- 本次问题：
- 环境：模型、GPU、服务端版本、客户端地址
- 执行命令：

```text
在这里粘贴完整命令
```

- 观察结果：
- 数据：请求数 / 并发度 / 平均延迟 / 吞吐 / token 数
- 我的解释：
- 还不确定的地方：
- 下一步最小实验：

## 第一个待完成实验

问题：同一个 prompt 下，把并发度从 1 提高到 2、4、8，吞吐和单请求延迟如何变化？

建议命令：

```powershell
vllm-lab benchmark --model <model-name> --requests 8 --concurrency 1
vllm-lab benchmark --model <model-name> --requests 8 --concurrency 2
vllm-lab benchmark --model <model-name> --requests 8 --concurrency 4
vllm-lab benchmark --model <model-name> --requests 8 --concurrency 8
```

先不要追求严谨压测；先把四次输出保存下来，并写三句话解释差异。
