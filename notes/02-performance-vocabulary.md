# 性能词汇卡片

## 延迟（latency）

一次请求从发出到收到结果花费的时间。本项目的 `average_latency_ms` 是客户端侧的粗粒度测量，包含网络、排队、服务端计算和响应传输。

## 吞吐（throughput）

单位时间完成的成功请求数。本项目用 `requests_per_second` 做入门级观察，不等同于严谨的 tokens/s 压测结果。

## Prefill

处理输入 prompt，建立生成所需的中间状态。长 prompt 通常会放大这一阶段的成本。

## Decode

逐 token 生成输出，并持续读取和更新 KV cache。输出更长时，decode 阶段通常更明显。

## Continuous batching

请求可以在不同时间到达并交错推进，而不是必须等一整个固定 batch 准备完成。第 4 天的并发实验是观察该思想的入口，不是对内部实现的完整证明。

## KV cache

保存注意力计算中可复用的 key/value 状态，避免生成每个新 token 时重复计算整个历史序列。后续要把这个概念连接到内存布局和块管理。
