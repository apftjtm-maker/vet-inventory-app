#!/usr/bin/env python3
"""라이브(GitHub Pages) URL 전수 검증 + 최종 스크린샷."""
import json, os, sys
from playwright.sync_api import sync_playwright

URL = "https://apftjtm-maker.github.io/vet-inventory-app/"
OUT = "/workspace/downloads"
os.makedirs("/workspace/work/vet-inventory-app/shots", exist_ok=True)
errors, console, results = [], [], []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))
    print(("PASS " if cond else "FAIL ") + name + (" · " + extra if extra else ""))


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1440, "height": 950}, locale="ko-KR",
                              permissions=["clipboard-read", "clipboard-write"])
    page = ctx.new_page()
    page.on("console", lambda m: console.append((m.type, m.text)))
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(URL, wait_until="load")
    page.wait_for_timeout(1500)

    check("프리셋 34종", page.locator(".row").count() == 34, f"rows={page.locator('.row').count()}")
    need = page.locator("#sumNeed").inner_text().replace("종", "").strip()
    check("발주 필요 8종", need == "8", f"need={need}")
    amt = page.locator("#sumAmt").inner_text()
    check("예상 발주 금액 표시", "원" in amt, amt)
    check("카테고리 칩 5개", page.locator(".chip-btn").count() == 5)

    # 칩 필터
    for cat, n in [("의약품", 12), ("수액·소모품", 12), ("사료·처방식", 6), ("검사·기타", 4)]:
        page.get_by_role("button", name=f"{cat} {n}").click()
        page.wait_for_timeout(180)
        got = page.locator(".row").count()
        check(f"필터 {cat} {n}종", got == n, f"rows={got}")
    page.get_by_role("button", name="전체 34").click()
    page.wait_for_timeout(150)

    # 검색
    page.fill("#search", "아조딜")
    page.wait_for_timeout(200)
    check("검색(아조딜) 1종", page.locator(".row").count() == 1)
    page.fill("#search", "")
    page.wait_for_timeout(150)

    # 수량 조절
    r0 = page.locator(".row").first
    c0 = int(r0.locator(".cur").inner_text())
    r0.get_by_title("1 빼기").click(); page.wait_for_timeout(200)
    c1 = int(page.locator(".row").first.locator(".cur").inner_text())
    page.locator(".row").first.get_by_title("1 더하기").click(); page.wait_for_timeout(200)
    c2 = int(page.locator(".row").first.locator(".cur").inner_text())
    check("-1/+1 동작", c1 == c0 - 1 and c2 == c0, f"{c0}->{c1}->{c2}")

    # 수정 모달
    page.locator(".row").first.get_by_title("수정").click()
    page.wait_for_timeout(300)
    check("수정 모달", page.locator("#editModal").is_visible())
    page.fill("#eSafe", "4")
    page.click("#editForm button[type=submit]")
    page.wait_for_timeout(300)
    check("수정 저장 반영", "안전 4" in page.locator(".row").first.inner_text())

    # 발주서 복사 + 클립보드
    page.locator(".vendor-actions button", has_text="발주서 복사").first.click()
    page.wait_for_timeout(500)
    clip = page.evaluate("navigator.clipboard.readText()")
    check("발주서 복사", "[발주 요청]" in clip and "수신:" in clip, clip.split("\n")[1] if clip else "empty")

    # 백업 저장
    with page.expect_download() as di:
        page.click("#exportBtn")
    d = di.value
    bp = "/workspace/work/vet-inventory-app/shots/live_backup.json"
    d.save_as(bp)
    data = json.load(open(bp, encoding="utf-8"))
    check("백업 저장", data["version"] == 2 and len(data["items"]) == 34, d.suggested_filename)

    # 백업 불러오기
    page.set_input_files("#importFile", bp)
    page.wait_for_timeout(800)
    check("백업 불러오기", page.locator(".row").count() == 34)

    # manifest / icons / sw
    man = page.evaluate("fetch('manifest.webmanifest').then(r=>r.json())")
    check("manifest name/short_name", man["short_name"] == "재고관리" and man["display"] == "standalone", man["name"])
    check("manifest 아이콘 3종", len(man["icons"]) == 3, str([i["sizes"] for i in man["icons"]]))
    for f in ["index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-512-maskable.png",
              "icon-180.png", "icon-32.png", "sw.js"]:
        r = page.request.get(URL + f)
        check(f"HTTP 200 {f}", r.status == 200, f"{r.status} {len(r.body())}B")

    page.wait_for_timeout(1500)
    sw = page.evaluate("navigator.serviceWorker.getRegistrations().then(a=>a.map(r=>({s:r.scope,a:!!r.active})).length ? a.map(r=>[r.scope,!!r.active]) : [])")
    check("서비스워커 active", bool(sw), str(sw))
    check("아이콘 표시(로고 이미지)", page.evaluate("document.querySelector('.logo').naturalWidth") > 0)

    # 설치 가능성(CDP)
    try:
        cdp = ctx.new_cdp_session(page)
        errs = cdp.send("Page.getInstallabilityErrors").get("installabilityErrors", [])
        check("Chrome 설치 가능성 오류 0", len(errs) == 0, str(errs))
    except Exception as e:
        print("SKIP installability:", e)

    # 새로고침 유지
    page.reload(wait_until="load"); page.wait_for_timeout(900)
    check("새로고침 유지", page.locator(".row").count() == 34)
    page.screenshot(path=os.path.join(OUT, "동물병원_재고앱_검수_데스크톱.png"))
    page.screenshot(path="/workspace/work/vet-inventory-app/shots/live_desktop_full.png", full_page=True)

    # 모바일
    m = ctx.new_page()
    m.on("pageerror", lambda e: errors.append("mobile: " + str(e)))
    m.set_viewport_size({"width": 390, "height": 844})
    m.goto(URL, wait_until="load")
    m.wait_for_timeout(1200)
    m.screenshot(path=os.path.join(OUT, "동물병원_재고앱_검수_모바일.png"))
    m.screenshot(path="/workspace/work/vet-inventory-app/shots/live_mobile_full.png", full_page=True)
    check("모바일 행 렌더", m.locator(".row").count() == 34)

    # 모바일 수정 버튼 접근
    m.locator(".row").first.get_by_title("수정").click()
    m.wait_for_timeout(400)
    check("모바일 수정 모달", m.locator("#editModal").is_visible())
    m.click("#editCancel")

    browser.close()

bad = [c for c in console if c[0] in ("error", "warning")]
print("\n--- 콘솔", len(console), "건 ---")
for c in console[-10:]:
    print(c)
print("pageerrors:", errors)
print("bad console:", bad)
fails = [r for r in results if not r[1]]
print(f"\n결과 {len(results)-len(fails)}/{len(results)} 통과")
sys.exit(1 if (fails or errors or bad) else 0)
