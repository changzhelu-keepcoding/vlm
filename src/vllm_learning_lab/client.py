"""A deliberately small OpenAI-compatible client for learning experiments."""

from dataclasses import dataclass
import json
from typing import Any, Callable
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class ChatResult:
    content: str
    model: str
    usage: Usage


PostJson = Callable[[str, dict[str, Any], dict[str, str], float], dict[str, Any]]


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    timeout: float,
) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class VLLMClient:
    """The smallest useful client for a vLLM OpenAI-compatible server."""

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str = "EMPTY",
        timeout: float = 60.0,
        post_json: PostJson | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._post_json = post_json or _post_json

    def chat(
        self,
        *,
        model: str,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 128,
        temperature: float = 0.0,
    ) -> ChatResult:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        response = self._post_json(
            f"{self.base_url}/v1/chat/completions",
            payload,
            {"Authorization": f"Bearer {self.api_key}"},
            self.timeout,
        )

        choices = response.get("choices") or []
        if not choices:
            raise ValueError("vLLM response did not contain choices")
        message = choices[0].get("message") or {}
        usage_data = response.get("usage") or {}
        usage = Usage(
            prompt_tokens=int(usage_data.get("prompt_tokens", 0)),
            completion_tokens=int(usage_data.get("completion_tokens", 0)),
            total_tokens=int(usage_data.get("total_tokens", 0)),
        )
        return ChatResult(
            content=str(message.get("content", "")),
            model=str(response.get("model", model)),
            usage=usage,
        )
