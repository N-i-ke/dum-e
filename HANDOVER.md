# dum-e 開発引き継ぎ書

前セッション(jarvis リポジトリでの設計フェーズ)からの引き継ぎドキュメント。
このリポジトリで開発を始めるセッションは、まず本書を読むこと。

## プロジェクト概要

**dum-e** は、完全無料で完結するローカル LLM パーソナルアシスタント。
Ollama 上のオープンウェイトモデルに J.A.R.V.I.S. の人格を焼き込み、
常駐する開発の相棒として育てる。名前の由来はトニー・スタークの工房の
ロボットアーム DUM-E。

## 絶対の制約

1. **完全無料で完結する** — API 課金を一切発生させない。
   クラウド LLM(Claude API 等)へのルーティングは実装しない
2. 人格・行動原則の単一情報源は `persona/JARVIS.md`。
   人格に関する変更はこのファイルにのみ加える

## 実行環境

- Mac (Apple Silicon M4 Pro / RAM 48GB / arm64)
- Ollama 0.32.1 導入済み(`brew services start ollama` で常駐中、port 11434)
- モデルは未ダウンロード(`ollama pull qwen3:14b` を 11% で中断した状態。再実行が必要)

## アーキテクチャ(5 層)

```
1. Interface     : CLI チャット → 将来: Open WebUI / 音声(Whisper + Kokoro TTS)
2. Orchestration : エージェントループ、ローカル二段ルーター(軽量⇔重量)
3. Persona       : persona/JARVIS.md をシステムプロンプトとして焼き込み
4. Memory        : 短期 = 会話履歴(SQLite) / 長期 = Markdown + RAG(ChromaDB)
5. Runtime       : Ollama(OpenAI 互換 API、localhost:11434)
```

### モデル選定

| 役割 | モデル | 備考 |
|---|---|---|
| 軽量級(常用) | Qwen3 14B (`qwen3:14b`, 約 9GB) | 日本語性能と速度の均衡 |
| 重量級(将来) | Qwen3-Coder 30B (MoE) | 総 30B・アクティブ約 3B。「大きいのに速い」。Phase 3 まで導入しない |
| embedding(将来) | nomic-embed-text or bge-m3 | RAG 用。Phase 2 で選定 |

## フェーズ計画

- **Phase 0**: 人格焼き込み — `persona/build.sh` で `jarvis-local` モデルを生成し、
  口調・行動原則の引き継ぎ具合を対話で検証する(スクリプト作成済み・未実行)
- **Phase 1**: CLI チャット + 人格 + 短期記憶(SQLite に会話履歴を永続化)。
  モデルは軽量級一本で始める
- **Phase 2**: 長期記憶 — Markdown ノート + RAG(ChromaDB + 多言語 embedding)
- **Phase 3**: ローカル二段ルーター — 14B で不足した実例が溜まってから重量級を導入
- **Phase 4**: 音声(Whisper STT + Kokoro TTS)・常駐化

実装言語は未決。前セッションの推奨は Python(LLM エコシステムの厚み)。

## 現状のファイル

- `HANDOVER.md` — 本書
- `persona/JARVIS.md` — 人格・行動原則の定義(小型モデル向けに凝縮済み)
- `persona/build.sh` — JARVIS.md をシステムプロンプトに埋め込んで
  `ollama create jarvis-local` を実行するスクリプト

## 設計判断の根拠(要約)

- 素のローカル LLM 単体は個人開発では価値が薄い。価値は人格 + 記憶 +
  ルーティングを束ねたシステム側に生まれる
- 「まず全部ローカル、不足した場面だけ上位へ」が 2026 年の定石ロールアウト。
  本プロジェクトでは上位もローカル(重量級モデル)とし、無料制約を守る
- Apple Silicon + Ollama(MLX 対応)は現在この分野の最適環境
- 二段構えは最初から作らない。軽量級で不足を感じた場面を記録し、
  実例をもって重量級の導入を判断する

## 参考リンク

- https://note.com/kaoru64/n/n7e47e4873d38 (ローカルLLMの実用性考察)
- https://usknet.com/dxgo/contents/dx-technology/what-is-a-local-llm/ (ローカルLLM概説)
- https://www.sitepoint.com/hybrid-cloudlocal-llm-the-complete-architecture-guide-2026/ (ハイブリッド設計)
- https://www.glukhov.org/ai-systems/ (アシスタントのシステム設計論)
- https://github.com/rezaulhreza/jarvis (類似 OSS の先行例)

## 次セッションの最初のアクション

1. `ollama pull qwen3:14b` を完走させる
2. `persona/build.sh` を実行して `jarvis-local` を生成
3. `ollama run jarvis-local` で人格の引き継ぎ具合を検証(Phase 0 完了判定)
4. Phase 1 の実装言語を決めて着手
