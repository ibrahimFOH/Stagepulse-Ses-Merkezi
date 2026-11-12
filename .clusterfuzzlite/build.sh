#!/bin/bash -eu

cd "$SRC/stagepulse"
for fuzzer in fuzz/*.py; do
  compile_python_fuzzer "$fuzzer"
done
