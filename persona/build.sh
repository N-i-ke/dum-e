#!/bin/bash
# JARVIS.md をシステムプロンプトとして埋め込んだ Ollama モデル `jarvis-local` を作成する。
# 使い方: ./build.sh [ベースモデル]  (デフォルト: qwen3:14b)
set -euo pipefail
cd "$(dirname "$0")"

BASE_MODEL="${1:-qwen3:14b}"

{
  echo "FROM ${BASE_MODEL}"
  echo "PARAMETER temperature 0.7"
  echo 'SYSTEM """'
  cat JARVIS.md
  echo '"""'
} > Modelfile

ollama create jarvis-local -f Modelfile
echo "done: ollama run jarvis-local で起動できます"
