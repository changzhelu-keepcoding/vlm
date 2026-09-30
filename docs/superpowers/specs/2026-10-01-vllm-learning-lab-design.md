# vLLM Learning Lab 设计规格

## 1. 背景与目标

`vllm-learning-lab` 是一个独立的、面向个人学习者的 vLLM 实验项目。它不重新实现 vLLM，也不把 vLLM 源码复制进本项目；它通过一个足够小的客户端和一组可复现实验，把可观察的服务现象连接到 vLLM 的运行原理和源码调用链。

第一阶段的目标是建立以下闭环：

```text
启动或连接服务 → 发起单请求 → 改变并发度 → 保存数据 → 解释现象 → 定向阅读源码
```

学习主线固定为：部署与 API → 延迟和吞吐 → prefill/decode → KV cache → continuous batching → 定向源码导读。

## 2. 用户与运行环境

- 主要使用者：已有 Python 基础、希望通过实验理解 vLLM 的个人学习者。
- 客户端：Windows 上运行 Python 项目。
- 服务端：优先支持 WSL2 中的 Linux GPU 环境，Docker 作为可选补充。
- 无 GPU 时：客户端单元测试和模拟实验仍可运行；真实服务实验不作为所有开发任务的前置条件。
- 模型基线：约 1.5B 参数的 instruct 模型。真实实验开始前，记录实际模型名和 vLLM 服务端版本。

## 3. 第一阶段范围

### 必须包含

1. `smoke`：向 OpenAI-compatible Chat Completions API 发送单次请求，并展示文本和 token usage。
2. `benchmark`：固定模型和 prompt，改变并发度 `1/2/4/8`，统计成功数、失败数、平均延迟、请求吞吐和 token 数。
3. JSON 运行记录：每次运行追加一份机器可读数据，不覆盖历史记录。
4. Markdown 学习记录：保存实验解释、推断、不确定性和下一步问题。
5. WSL2 主路径说明，以及 Docker 补充启动示例。
6. 可选 upstream 获取脚本：按用户指定的 vLLM 版本下载或更新源码，不把源码复制进学习项目。
7. 单元测试和模拟客户端，使没有 GPU 或服务端时也能验证核心行为。
8. 第一阶段学习报告：解释 prefill、decode、KV cache、continuous batching，并完成至少一条源码调用链导读。

### 明确不包含

- Web Dashboard。
- 交互式聊天界面、模型管理和配置中心。
- 自动重试、复杂的压测编排或完整服务生命周期管理。
- 第一阶段的 p95、TTFT、GPU 显存监控和 tokens/s 专项分析；这些属于后续扩展。
- 复制、维护或修改 vLLM 源码。
- 以提交 vLLM Pull Request 作为第一阶段完成条件。

## 4. 用户流程

### 4.1 安装与离线验证

用户可以在项目根目录执行可编辑安装和测试。即使没有 vLLM 服务，以下能力也必须可用：

- 解析 CLI 参数。
- 构造 OpenAI-compatible 请求。
- 解析成功响应和 token usage。
- 处理空 choices 响应。
- 并发执行、统计成功/失败和生成 JSON 运行记录。

### 4.2 单请求实验

用户提供 base URL、API key、模型名和 prompt。客户端将系统消息（如果有）、用户消息、模型名和采样参数发送到 `/v1/chat/completions`，然后显示生成内容和 usage。API key 可以用于请求，但不得写入运行记录。

### 4.3 并发实验

用户固定模型和 prompt，只改变并发度。一个失败请求不能终止整组实验；实验结束后，成功结果、失败原因和汇总指标一起落盘。实验结果必须包含足够的配置，让后续能够区分不同并发度、模型和服务端版本。

### 4.4 源码导读

用户先从实验记录中选一个现象，再查看对应版本的 upstream 源码。每次导读记录：vLLM 版本、文件路径、函数或类、实验现象、实际解释和未解决问题。导读追踪最小必要调用链，不要求通读整个仓库。

## 5. 组件与边界

### `client`

负责 HTTP 请求、请求 JSON 组装和响应解析。它不负责并发调度、重试、指标聚合或源码学习记录。

### `benchmark`

负责并发提交请求、测量客户端侧延迟、收集成功/失败和汇总指标。它依赖一个具有 `chat` 行为的客户端接口，不依赖具体 HTTP 实现，以便使用真实客户端或模拟客户端。

### `run recorder`

负责为一次实验生成 JSON 记录。它只记录实验配置、指标、错误和时间信息，不保存 API key。它不负责解释实验结果。

### `learning notes`

负责保存人的解释和问题，使用 Markdown。它不作为机器指标数据库，也不承担自动报表生成。

### `upstream helper`

负责按明确版本获取 vLLM 源码，并输出源码位置和版本信息。它不修改学习项目的业务代码，也不承诺多版本兼容。

## 6. 数据流

```text
CLI 参数
  ↓
VLLMClient
  ↓  POST /v1/chat/completions
ChatResult
  ↓
Benchmark（并发、计时、错误收集）
  ↓
Run Recorder（JSON）
  ↓
Study Log / Learning Report（Markdown 解释）
```

客户端侧延迟从请求发出前开始计时，到收到并解析响应后结束。它是端到端的粗粒度观察值，包含网络、服务端排队、计算和响应传输；文档必须明确它不等同于 TTFT 或 GPU kernel 时间。

## 7. 运行记录约定

每次 benchmark 追加一份独立 JSON 文件，至少包含：

- 运行时间和实验名称。
- 客户端项目版本。
- 服务端 base URL（不包含 API key）。
- vLLM 服务端版本（真实服务实验必填）。
- 模型名、prompt、请求总数和并发度。
- 成功数、失败数、平均延迟、请求吞吐和 token 总数。
- 每个失败的错误类型和消息。

第一阶段不要求设计跨版本数据库或复杂 schema migration；JSON 文件是可读、可复制、可删除的实验快照。

## 8. 错误处理

- HTTP 或连接错误：归类为当前请求失败，并继续处理同一批次的其他请求。
- 响应缺少 `choices`：视为协议响应错误，记录明确的 `ValueError` 信息。
- `concurrency < 1`：在 CLI 或 benchmark 入口尽早拒绝。
- API key：只进入请求 header，不进入日志、JSON 或报告。
- 没有服务端：不把它当作单元测试失败；运行离线测试，并提示需要真实服务才能完成 smoke 验收。

## 9. 测试策略

第一阶段测试分三层：

1. 客户端行为测试：验证请求 URL、header、messages、参数和响应解析。
2. benchmark 行为测试：验证并发、成功/失败统计、延迟、吞吐和 token 汇总。
3. CLI 行为测试：验证子命令参数解析和汇总输出格式。

真实服务 smoke 和 `1/2/4/8` 并发实验属于手工验收，不在无 GPU 的单元测试套件中伪装成已完成。

## 10. 第一阶段验收标准

- 完整测试套件通过。
- `smoke` 能连接一个真实 vLLM OpenAI-compatible 服务。
- 使用同一模型和 prompt 完成并保存并发度 `1/2/4/8` 的四组实验。
- 运行记录不泄露 API key，且能区分模型、并发度和服务端版本。
- 学习报告解释 prefill、decode、KV cache、continuous batching 的基本关系。
- 至少完成一条从实验现象到 upstream 源码函数/类的调用链导读。
- 无服务端时，离线单元测试和模拟实验仍然可运行。

## 11. 后续扩展顺序

第一阶段验收后，按以下顺序扩展：

1. p50/p95、TTFT 和生成 tokens/s。
2. 输入长度、输出长度和 prompt 类型对比。
3. GPU 显存和服务端日志关联。
4. prefix caching、量化或 speculative decoding 专题。
5. 从学习实验演化为可视化报告，而不是直接跳到 Web Dashboard。
