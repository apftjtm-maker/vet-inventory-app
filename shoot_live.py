#!/usr/bin/env python3
"""라이브 URL 초기 상태(저장값 없음) 스크린샷 — 데스크톱/모바일."""
import os
from playwright.sync_api import sync_playwright

URL = "https://apftjtm-maker.github.io/vet-inventory-app/"
OUT = "/workspace/downloads"
S = "/workspace/work/vet-inventory-app/shots"

with sync_playwright() as p:
    b = p.chromium.launch()

    # 데스크톱
    c1 = b.new_context(viewport={"width": 1440, "height": 980}, locale="ko-KR")
    pg = c1.new_page()
    pg.goto(URL, wait_until="load")
    pg.wait_for_timeout(1800)
    pg.screenshot(path=os.path.join(OUT, "동물병원_재고앱_검수_데스크톱.png"))
    pg.screenshot(path=os.path.join(S, "live_desktop_full.png"), full_page=True)

    # 수정 모달 화면
    pg.locator(".row").first.get_by_title("수정").click()
    pg.wait_for_timeout(500)
    pg.screenshot(path=os.path.join(S, "live_edit_modal.png"))
    pg.click("#editCancel")

    # 모바일 (갤럭시 크기)
    c2 = b.new_context(viewport={"width": 390, "height": 844}, locale="ko-KR",
                       device_scale_factor=2, is_mobile=True, has_touch=True,
                       user_agent="Mozilla/5.0 (Linux; Android 15; SM-S938N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36")
    pm = c2.new_page()
    pm.goto(URL, wait_until="load")
    pm.wait_for_timeout(1800)
    pm.screenshot(path=os.path.join(OUT, "동물병원_재고앱_검수_모바일.png"))
    pm.screenshot(path=os.path.join(S, "live_mobile_full.png"), full_page=True)

    for pth in [os.path.join(OUT, "동물병원_재고앱_검수_데스크톱.png"),
                os.path.join(OUT, "동물병원_재고앱_검수_모바일.png")]:
        print(pth, os.path.getsize(pth))
    b.close()
