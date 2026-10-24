#!/usr/bin/env bash
# Render an SVG to PNG at WxH via headless Chrome. usage: render.sh in.svg out.png W H
set -e
tmp=$(mktemp -d); html="$tmp/p.html"
printf '<html><body style="margin:0;background:transparent"><img src="file://%s" width="%s" height="%s" style="display:block"></body></html>' "$(realpath "$1")" "$3" "$4" > "$html"
google-chrome --headless=new --no-sandbox --disable-gpu --hide-scrollbars --default-background-color=00000000 \
  --force-device-scale-factor=1 --window-size="$3,$4" --screenshot="$tmp/o.png" "file://$html" >/dev/null 2>&1
mv "$tmp/o.png" "$2"; rm -rf "$tmp"
