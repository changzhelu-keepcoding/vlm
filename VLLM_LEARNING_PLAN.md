# vLLM 项目学习计划

## 目标

用两周建立一条从“能部署和调用”到“能解释关键性能现象”的路径，最终能回答：

- 一个请求从 API 进入服务端后，大致经过哪些阶段？
- 为什么多个请求交错生成时，GPU 利用率和吞吐通常更好？
- KV cache 为什么需要分页或块管理？
- `prompt_tokens`、`completion_tokens`、延迟和吞吐如何一起看？
- 如果要贡献代码，应该从哪一层开始定位？

## 第 1 周：先跑通，再测量

### 第 1 天：读项目和建立基线

- 阅读 `README.md` 和本文件。
- 阅读 `src/vllm_learning_lab/client.py`。
- 运行测试，理解 `payload → response → ChatResult`。
- 记录：OpenAI 兼容接口给客户端带来了什么好处？

### 第 2 天：单请求链路

- 启动一个可访问的 vLLM 服务。
- 运行 `smoke` 命令。
- 改变 `max_tokens` 和 prompt 长度。
- 记录返回内容、`usage` 和主观等待时间。

### 第 3 天：延迟拆分

- 阅读 `benchmark.py`，标出计时开始和结束的位置。
- 让 `concurrency=1`，分别改变 prompt 长度和输出长度。
- 记录平均延迟，不急着下结论：当前实验还没有区分排队、tokenize、prefill 和 decode。

### 第 4 天：并发实验

- 固定模型和 prompt，依次测试 `concurrency=1/2/4/8`。
- 记录成功数、失败数、平均延迟、requests/s、token 数。
- 观察吞吐上升时，单请求延迟是否也上升。

### 第 5 天：形成第一张对比表

- 把第 3、4 天数据写进 `STUDY_LOG.md`。
- 用自己的话解释“吞吐”和“延迟”的区别。
- 写出一个反直觉现象：为什么并发更多不一定让每个请求更快？

## 第 2 周：从现象回到原理和源码

### 第 6 天：prefill vs decode

- 用长 prompt、短输出和短 prompt、长输出版做对比。
- 关注 token 数与延迟的关系。
- 在 `notes/` 新建一页笔记，画出 prefill/decode 的简图。

### 第 7 天：KV cache

- 阅读 `notes/01-api-path.md`，把“请求层概念”连接到模型执行。
- 用自己的话解释：KV cache 缓存的是什么，为什么能避免重复计算。
- 记录一个仍然不懂的问题。

### 第 8 天：PagedAttention 和块管理

- 从官方论文或 vLLM 相关文档开始，不要求当天读完源码。
- 画出“请求 → token block → KV cache block”的关系。
- 比较连续内存分配和块式管理的优缺点。

### 第 9 天：调度器与 continuous batching

- 用并发实验结果反推调度问题：谁先运行、谁继续 decode、谁等待资源？
- 在源码中只追一条调用链，不做全仓库漫游。
- 把调用链和猜想写进 `STUDY_LOG.md`。

### 第 10 天：小结和下一阶段

- 写一页“我现在能解释什么”的总结。
- 选择一个方向：量化、prefix caching、speculative decoding 或源码贡献。
- 为下一轮学习写一个可验证的问题，而不是写“继续看源码”。

## 完成标准

- 能独立启动或连接一个 vLLM OpenAI-compatible 服务。
- 能解释本项目客户端的请求和响应结构。
- 至少完成一组不同并发度的对比实验。
- 能区分 prefill、decode、KV cache、batching 的角色。
- 有一份带数据、命令和解释的学习记录，而不是只有链接收藏。
