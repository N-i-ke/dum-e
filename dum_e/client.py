"""Ollama /api/chat のストリーミングクライアント。標準ライブラリのみで実装。"""

import json
import urllib.error
import urllib.request
from collections.abc import Iterator

OLLAMA_HOST = "http://localhost:11434"
DEFAULT_MODEL = "jarvis-local"


class OllamaError(RuntimeError):
    pass


def chat_stream(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    host: str = OLLAMA_HOST,
) -> Iterator[str]:
    """メッセージ列を送信し、応答テキストを断片単位で yield する。

    人格はモデル(jarvis-local)側に焼き込み済みのため、
    system メッセージはここでは付与しない。
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        # qwen3 の思考モードは応答前の長考で体感速度を落とすため無効化する
        "think": False,
    }
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                chunk = json.loads(line)
                if chunk.get("error"):
                    raise OllamaError(chunk["error"])
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
                if chunk.get("done"):
                    return
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise OllamaError(f"Ollama がエラーを返しました: {detail}") from e
    except urllib.error.URLError as e:
        raise OllamaError(
            f"Ollama に接続できません ({host})。"
            f" `brew services start ollama` を確認してください: {e.reason}"
        ) from e
