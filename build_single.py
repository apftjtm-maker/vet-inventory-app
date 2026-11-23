#!/usr/bin/env python3
"""index.html → 단일 HTML 백업본(다운로드용). 아이콘을 data URI로 인라인.
   © 온마루 동물메디컬센터 원장 이용민. All rights reserved."""
import base64, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = "/workspace/downloads/동물병원_재고부족_자동발주_체크앱.html"


def data_uri(name, mime="image/png"):
    with open(os.path.join(ROOT, name), "rb") as f:
        return "data:%s;base64,%s" % (mime, base64.b64encode(f.read()).decode())


html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

# manifest는 파일 옆에 있어야 동작하므로 단일 파일본에서는 제거
html = re.sub(r'\n<link rel="manifest"[^>]*>', "\n<!-- 단일 파일 백업본: manifest 없음(파일 옆에 두는 배포본에서만 동작) -->", html)

icon32 = data_uri("icon-32.png")
icon192 = data_uri("icon-192.png")
icon180 = data_uri("icon-180.png")

html = html.replace('<link rel="icon" href="icon-32.png" sizes="32x32" type="image/png">',
                    '<link rel="icon" href="%s" sizes="32x32" type="image/png">' % icon32)
html = html.replace('<link rel="icon" href="icon-192.png" sizes="192x192" type="image/png">',
                    '<link rel="icon" href="%s" sizes="192x192" type="image/png">' % icon192)
html = html.replace('<link rel="apple-touch-icon" href="icon-180.png">',
                    '<link rel="apple-touch-icon" href="%s">' % icon180)
html = html.replace('<img class="logo" src="icon-192.png"', '<img class="logo" src="%s"' % icon192)

open(OUT, "w", encoding="utf-8").write(html)
print(OUT, len(html), "bytes")
