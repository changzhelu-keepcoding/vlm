# 从客户端请求到可观察结果

本项目把一次聊天请求压缩成四个学习对象：

```text
prompt
  ↓
messages + sampling 参数
  ↓  POST /v1/chat/completions
choices[0].message.content + usage
  ↓
ChatResult
```

## 先看客户端

`client.py` 做三件事：

1. 把系统提示词、用户 prompt、模型名和采样参数组装成 JSON。
2. 通过 HTTP POST 发到 `/v1/chat/completions`。
3. 从响应中提取 `choices[0].message.content` 和 token usage。

它没有实现 batching、KV cache 或 GPU 调度；这些是服务端要学习的部分。客户端的价值是提供一个稳定观测面：你可以改变输入和并发度，再把结果与服务端原理对应起来。

## 带着问题读服务端

- 请求进入后，什么时候完成 tokenization？
- 哪一步把请求放进等待队列？
- prefill 和 decode 是否使用同一个调度路径？
- `usage` 是在哪里统计的？
- 一个请求如何知道自己拥有哪一部分 KV cache？

每次只追一个问题。找到代码后，把“文件、函数、我原来的猜想、实际发现”写入 `STUDY_LOG.md`。
