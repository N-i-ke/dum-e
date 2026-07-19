"""CLI チャット。会話履歴を SQLite に保存し、セッションを跨いで文脈を保持する。"""

import argparse
import sys

from .client import DEFAULT_MODEL, OllamaError, chat_stream
from .memory import Memory

# モデルに渡す直近メッセージ数。コンテキスト長と応答速度の均衡点
HISTORY_WINDOW = 20

USAGE = "/new: 新規セッション  /flag <理由>: 不足の記録  /bye: 終了"


def show_flags(memory: Memory) -> None:
    rows = memory.flags()
    if not rows:
        print("dum-e: 記録された不足事例はありません")
        return
    for flag_id, created_at, reason, context in rows:
        print(f"[{flag_id}] {created_at}  {reason}")
        for line in context.splitlines():
            print(f"    {line}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="dum-e", description="ローカル LLM パーソナルアシスタント dum-e"
    )
    parser.add_argument(
        "--new", action="store_true", help="履歴を引き継がず新規セッションで開始する"
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="使用する Ollama モデル")
    parser.add_argument(
        "--flags", action="store_true", help="記録済みの不足事例を一覧して終了する"
    )
    args = parser.parse_args()

    memory = Memory()
    if args.flags:
        show_flags(memory)
        memory.close()
        return
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
            if user_input == "/bye":
                break
            if user_input == "/new":
                session_id = memory.new_session()
                print(f"dum-e: 新規セッション {session_id} を開始しました")
                continue
            if user_input.startswith("/flag"):
                reason = user_input.removeprefix("/flag").strip()
                if not reason:
                    print("dum-e: 理由を添えてください(例: /flag 日本語が崩れた)")
                    continue
                # 不足が起きた証拠として直前の往復を添える
                context = "\n".join(
                    f"{m['role']}: {m['content']}"
                    for m in memory.recent(session_id, 2)
                )
                memory.add_flag(session_id, reason, context)
                print("dum-e: 不足事例を記録しました(--flags で一覧)")
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
