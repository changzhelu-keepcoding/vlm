# vLLM Learning Lab

这是一个用来学习 vLLM 推理服务的最小项目。它不重新实现 vLLM，而是从一个真实的 OpenAI 兼容客户端出发，逐步观察：

1. 请求如何从客户端进入 `/v1/chat/completions`。
2. `choices` 和 `usage` 如何变成应用层结果。
3. 并发请求下，延迟、成功率、token 数和吞吐如何变化。
4. 这些现象如何对应到 vLLM 的 continuous batching、KV cache 和调度器。

vLLM 官方文档说明，服务端可以通过 `vllm serve` 启动，并提供 OpenAI-compatible Chat Completions API：
<https://docs.vllm.ai/en/latest/serving/online_serving/openai_compatible_server/>

## 目录

```text
.
├── src/vllm_learning_lab/
│   ├── client.py       # 最小 HTTP 客户端：协议与结果解析
│   ├── benchmark.py    # 并发实验：延迟、失败、吞吐统计
│   └── cli.py          # smoke / benchmark 命令
├── tests/              # 先写的行为测试
├── notes/              # 概念笔记
├── VLLM_LEARNING_PLAN.md
└── STUDY_LOG.md
```

## 安装与测试

PowerShell：

```powershell
python -m pip install -e . --no-deps
python -m unittest discover -s tests -v
```

项目运行时不依赖第三方 Python 包；`vllm` 服务端可以在另一台 GPU 主机、WSL2 或容器中运行，客户端只需要能访问 HTTP 地址。

## 连接 vLLM 服务

服务端示例（模型名仅作示例，请按机器显存和模型许可选择）：

```bash
vllm serve <model-name> --api-key learning-key
```

单次请求：

```powershell
vllm-lab --base-url http://localhost:8000 --api-key learning-key smoke `
  --model <model-name> `
  --prompt "用一句话解释 KV cache。"
```

并发实验：

```powershell
vllm-lab --base-url http://localhost:8000 --api-key learning-key benchmark `
  --model <model-name> `
  --requests 8 `
  --concurrency 2
```

如果不想安装命令，也可以直接运行：

```powershell
$env:PYTHONPATH = "src"
python -m vllm_learning_lab --help
```

## 学习顺序

先读 [VLLM_LEARNING_PLAN.md](VLLM_LEARNING_PLAN.md)，每完成一次实验就把命令、现象和解释写入 [STUDY_LOG.md](STUDY_LOG.md)。

不要一开始就通读整个 vLLM 仓库：先用这个项目制造一个可观察的现象，再带着问题去找服务端代码。
