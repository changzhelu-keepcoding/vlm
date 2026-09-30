import unittest

from vllm_learning_lab.client import ChatResult, VLLMClient


class VLLMClientTests(unittest.TestCase):
    def test_chat_builds_openai_request_and_parses_response(self):
        captured = {}

        def post_json(url, payload, headers, timeout):
            captured.update(
                url=url,
                payload=payload,
                headers=headers,
                timeout=timeout,
            )
            return {
                "model": "Qwen/Qwen2.5-1.5B-Instruct",
                "choices": [
                    {"message": {"role": "assistant", "content": "你好，vLLM！"}}
                ],
                "usage": {
                    "prompt_tokens": 5,
                    "completion_tokens": 7,
                    "total_tokens": 12,
                },
            }

        client = VLLMClient(
            "http://localhost:8000/",
            api_key="test-key",
            post_json=post_json,
        )

        result = client.chat(
            model="Qwen/Qwen2.5-1.5B-Instruct",
            prompt="介绍一下 continuous batching",
            system="你是一个简洁的老师。",
            max_tokens=64,
            temperature=0.2,
        )

        self.assertIsInstance(result, ChatResult)
        self.assertEqual(result.content, "你好，vLLM！")
        self.assertEqual(result.usage.total_tokens, 12)
        self.assertEqual(captured["url"], "http://localhost:8000/v1/chat/completions")
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-key")
        self.assertEqual(captured["payload"]["messages"][0]["role"], "system")
        self.assertEqual(captured["payload"]["messages"][1]["content"], "介绍一下 continuous batching")

    def test_chat_rejects_response_without_choices(self):
        client = VLLMClient(
            "http://localhost:8000",
            post_json=lambda *args: {"model": "demo", "choices": []},
        )

        with self.assertRaises(ValueError):
            client.chat(model="demo", prompt="hello")


if __name__ == "__main__":
    unittest.main()
