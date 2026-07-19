"""CLI チャット。会話履歴を SQLite に保存し、セッションを跨いで文脈を保持する。"""

import argparse
import sys

from .client import DEFAULT_MODEL, OllamaError, chat_stream
from .memory import Memory

# モデルに渡す直近メッセージ数。コンテキスト長と応答速度の均衡点
HISTORY_WINDOW = 20

USAGE = "/new: 新規セッション  /bye: 終了"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dum-e", description="ローカル LLM パーソナルアシスタント dum-e"
    )
    parser.add_argument(
        "--new", action="store_true", help="履歴を引き継がず新規セッションで開始する"
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="使用する Ollama モデル")
    args = parser.parse_args()

    memory = Memory()
    session_id = memory.new_session() if args.new else memory.resume_or_create_session()
    print(f"dum-e: session {session_id} ({USAGE})")

    try:
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input in ("/bye", "/quit", "exit"):
                break
            if user_input == "/new":
                session_id = memory.new_session()
                print(f"dum-e: 新規セッション {session_id} を開始しました")
                continue

            messages = memory.recent(session_id, HISTORY_WINDOW)
            messages.append({"role": "user", "content": user_input})

            reply_parts: list[str] = []
            try:
                for part in chat_stream(messages, model=args.model):
                    print(part, end="", flush=True)
                    reply_parts.append(part)
            except OllamaError as e:
                print(f"\ndum-e: {e}", file=sys.stderr)
                continue
            print()

            # 応答が完了した往復のみ記憶する(失敗した呼び出しで履歴を汚さない)
            memory.add(session_id, "user", user_input)
            memory.add(session_id, "assistant", "".join(reply_parts))
    finally:
        memory.close()


if __name__ == "__main__":
    main()
