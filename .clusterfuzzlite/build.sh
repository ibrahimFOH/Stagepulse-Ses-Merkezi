#!/bin/bash -eu

cd "$SRC/stagepulse"
for fuzzer in "$SRC"/stagepulse/fuzz/*.py; do
  fuzzer_basename="$(basename -s .py "$fuzzer")"
  fuzzer_package="${fuzzer_basename}.pkg"
  pyinstaller --distpath "$OUT" --onefile --name "$fuzzer_package" "$fuzzer"
  cat > "$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
this_dir=\$(dirname "\$0")
ASAN_OPTIONS=\$ASAN_OPTIONS:symbolize=1:external_symbolizer_path=\$this_dir/llvm-symbolizer:detect_leaks=0 \
  "\$this_dir/$fuzzer_package" "\$@"
EOF
  chmod +x "$OUT/$fuzzer_basename"
done
