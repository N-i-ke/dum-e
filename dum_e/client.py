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
    think: bool = False,
) -> Iterator[tuple[str, str]]:
    """メッセージ列を送信し、("thinking" | "content", テキスト断片) を yield する。

    人格はモデル(jarvis-local)側に焼き込み済みのため、
    system メッセージはここでは付与しない。
    qwen3 の思考モードは既定で無効(応答前の長考で体感速度を落とすため)。
    推論が必要な質問では think=True で精度を優先できる。
    """
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": think,
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
                message = chunk.get("message", {})
                if thinking := message.get("thinking", ""):
                    yield "thinking", thinking
                if content := message.get("content", ""):
                    yield "content", content
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
