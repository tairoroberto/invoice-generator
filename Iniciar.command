#!/bin/zsh
cd "${0:A:h}"
PYTHON='/Users/tairo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
if [[ ! -x "$PYTHON" ]]; then PYTHON=python3; fi
if ! "$PYTHON" -c 'import reportlab' 2>/dev/null; then
  echo 'Instale a dependência: python3 -m pip install -r requirements.txt'
  read; exit 1
fi
open 'http://127.0.0.1:8765'
"$PYTHON" server.py
