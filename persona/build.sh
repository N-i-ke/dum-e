#!/bin/bash
# JARVIS.md をシステムプロンプトとして埋め込んだ Ollama モデル `jarvis-local` を作成する。
#
# 使い方:
#   ./build.sh                    搭載 RAM からプロファイルを自動選択
#   ./build.sh --profile lite     プロファイルを明示指定 (standard | lite | lite-alt)
#   ./build.sh <ベースモデル>      ベースモデルを直接指定 (num_ctx は 16384)
#
# プロファイル:
#   standard : RAM 32GB 以上向け。qwen3:14b-q8_0 / num_ctx 16384
#   lite     : RAM 16GB 向け。qwen3:14b (Q4)   / num_ctx 8192
#   lite-alt : lite でも重い機体向け。qwen3:8b / num_ctx 8192
set -euo pipefail
cd "$(dirname "$0")"

PROFILE=""
BASE_MODEL=""
NUM_CTX=16384

if [ "${1:-}" = "--profile" ]; then
  PROFILE="${2:?使い方: ./build.sh --profile <standard|lite|lite-alt>}"
elif [ -n "${1:-}" ]; then
  BASE_MODEL="$1"
fi

if [ -z "$BASE_MODEL" ]; then
  if [ -z "$PROFILE" ]; then
    # KV キャッシュ分も含めた実効メモリで判定する (16GB 機に q8_0 は載らない)
    mem_gb=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    if [ "$mem_gb" -ge 32 ]; then PROFILE="standard"; else PROFILE="lite"; fi
    echo "RAM ${mem_gb}GB を検出: プロファイル ${PROFILE} を選択"
  fi
  case "$PROFILE" in
    standard) BASE_MODEL="qwen3:14b-q8_0"; NUM_CTX=16384 ;;
    lite)     BASE_MODEL="qwen3:14b";      NUM_CTX=8192  ;;
    lite-alt) BASE_MODEL="qwen3:8b";       NUM_CTX=8192  ;;
    *) echo "不明なプロファイル: ${PROFILE} (standard | lite | lite-alt)" >&2; exit 1 ;;
  esac
fi

echo "base=${BASE_MODEL} num_ctx=${NUM_CTX}"

{
  echo "FROM ${BASE_MODEL}"
  echo "PARAMETER temperature 0.7"
  echo "PARAMETER num_ctx ${NUM_CTX}"
  echo 'SYSTEM """'
  cat JARVIS.md
  echo '"""'
} > Modelfile

ollama create jarvis-local -f Modelfile
echo "done: ollama run jarvis-local で起動できます"
