# dum-e

完全無料で完結するローカル LLM パーソナルアシスタント。
Ollama 上のオープンウェイトモデルに J.A.R.V.I.S. の人格を焼き込み、
常駐する開発の相棒として育てる。

設計の全体像と経緯は [HANDOVER.md](HANDOVER.md) を参照。

## 必要環境

- macOS (Apple Silicon 推奨) / Python 3.10+
- [Ollama](https://ollama.com)(`brew install ollama && brew services start ollama`)

## セットアップ

```sh
ollama pull qwen3:14b   # ベースモデル(約 9GB)
./persona/build.sh      # 人格を焼き込んだ jarvis-local を生成
```

## 使い方

```sh
python3 -m dum_e          # 前回セッションの続きから再開
python3 -m dum_e --new    # 新規セッションで開始
python3 -m dum_e --flags  # 記録済みの不足事例を一覧
```

- 会話履歴は `data/memory.db`(SQLite)に保存され、セッションを跨いで文脈を保持する
- チャット内コマンド:
  - `/new` — 新規セッション
  - `/flag <理由>` — モデルや記憶の不足事例を直前のやり取り付きで記録
    (重量級モデルや長期記憶を導入するかの判断材料。HANDOVER.md のフェーズ計画を参照)
  - `/bye` — 終了
- 外部依存なし(Python 標準ライブラリのみ)

## テスト

```sh
python3 -m unittest discover tests
```

## 人格の変更

人格・行動原則の単一情報源は `persona/JARVIS.md`。
変更後は `./persona/build.sh` で再ビルドする。
