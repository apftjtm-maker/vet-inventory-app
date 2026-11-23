#!/usr/bin/env python3
"""로컬 서버에서 앱 기능 전수 검증 + 스크린샷."""
import json, os, subprocess, sys, time, threading, http.server, socketserver, functools

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 0
SHOTS = os.path.join(ROOT, "shots")
os.makedirs(SHOTS, exist_ok=True)

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # 조용히
        pass

socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", PORT), functools.partial(Q, directory=ROOT))
PORT = srv.server_address[1]
th = threading.Thread(target=srv.serve_forever, daemon=True)
th.start()
time.sleep(0.3)

errors, console = [], []
results = []

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

    page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load")
    page.wait_for_timeout(700)

    # 1) 기본 데이터
    rows = page.locator(".row").count()
    check("프리셋 34종 렌더", rows == 34, f"rows={rows}")
    need = page.locator("#sumNeed").inner_text().replace("종", "").strip()
    check("발주 필요 8종", need == "8", f"need={need}")
    allc = page.locator("#sumAll").inner_text().replace("종", "").strip()
    check("전체 34종", allc == "34", f"all={allc}")
    chips = page.locator(".chip-btn").count()
    check("카테고리 칩 5개", chips == 5, f"chips={chips}")

    # 2) 카테고리 필터
    page.get_by_role("button", name="의약품 12").click()
    page.wait_for_timeout(200)
    r2 = page.locator(".row").count()
    check("의약품 필터 12종", r2 == 12, f"rows={r2}")
    page.get_by_role("button", name="전체 34").click()
    page.wait_for_timeout(150)
    check("전체 복귀 34종", page.locator(".row").count() == 34)

    # 3) 검색·거래처 필터·발주필요만
    page.fill("#search", "넥스가드")
    page.wait_for_timeout(200)
    check("검색 1종", page.locator(".row").count() == 1, f"rows={page.locator('.row').count()}")
    page.fill("#search", "")
    page.wait_for_timeout(150)
    page.select_option("#vendorFilter", "벳화점")
    page.wait_for_timeout(200)
    vb = page.locator(".row").count()
    check("거래처 필터(벳화점) 10종", vb == 10, f"rows={vb}")
    page.select_option("#vendorFilter", "all")
    page.check("#onlyNeed")
    page.wait_for_timeout(200)
    check("발주 필요만 8종", page.locator(".row").count() == 8, f"rows={page.locator('.row').count()}")
    page.uncheck("#onlyNeed")
    page.wait_for_timeout(150)

    # 4) 수량 -1 / +1 (첫 행: 넥스가드 stock 2)
    first = page.locator(".row").first
    cur0 = int(first.locator(".cur").inner_text())
    first.get_by_title("1 더하기").click()
    page.wait_for_timeout(250)
    cur1 = int(page.locator(".row").first.locator(".cur").inner_text())
    check("+1 반영", cur1 == cur0 + 1, f"{cur0}->{cur1}")
    page.locator(".row").first.get_by_title("1 빼기").click()
    page.wait_for_timeout(250)
    cur2 = int(page.locator(".row").first.locator(".cur").inner_text())
    check("-1 반영", cur2 == cur0, f"{cur1}->{cur2}")

    # 5) 품목 수정 모달
    page.locator(".row").first.get_by_title("수정").click()
    page.wait_for_timeout(300)
    check("수정 모달 열림", page.locator("#editModal").is_visible())
    page.fill("#eStock", "11")
    page.fill("#ePrice", "52000")
    page.fill("#eSpec", "3정/박스(신)")
    page.select_option("#eCat", "사료·처방식")
    page.click("#editForm button[type=submit]")
    page.wait_for_timeout(400)
    check("수정 모달 닫힘", not page.locator("#editModal").is_visible())
    row1 = page.locator(".row").first
    txt = row1.inner_text()
    check("수정 반영(현재고 11)", "11" in row1.locator(".cur").inner_text(), row1.locator(".cur").inner_text())
    check("수정 반영(카테고리)", "사료·처방식" in txt)
    check("수정 반영(규격)", "3정/박스(신)" in txt)
    # 되돌리기
    page.locator(".row").first.get_by_title("수정").click()
    page.wait_for_timeout(250)
    page.fill("#eStock", "2"); page.fill("#ePrice", "49000"); page.fill("#eSpec", "3정/박스")
    page.select_option("#eCat", "의약품")
    page.click("#editForm button[type=submit]")
    page.wait_for_timeout(300)

    # 6) 새 품목 추가
    page.click("details.add summary")
    page.wait_for_timeout(200)
    page.fill("#fName", "테스트 품목 A")
    page.fill("#fVendor", "테스트약품")
    page.select_option("#fCat", "수액·소모품")
    page.fill("#fStock", "1")
    page.fill("#fSafe", "3")
    page.fill("#fQty", "2")
    page.fill("#fPrice", "1000")
    page.click("#addForm button[type=submit]")
    page.wait_for_timeout(400)
    check("새 품목 추가 35종", page.locator(".row").count() == 35, f"rows={page.locator('.row').count()}")

    # 7) 발주서 복사
    page.locator(".vendor-actions button", has_text="발주서 복사").first.click()
    page.wait_for_timeout(500)
    toast = page.locator("#toast").inner_text()
    check("발주서 복사 토스트", "복사" in toast, toast)
    clip = page.evaluate("navigator.clipboard.readText()")
    check("클립보드에 발주서", "[발주 요청]" in clip, clip.split("\n")[0] if clip else "empty")

    # 미리보기
    page.locator(".vendor-actions button", has_text="미리보기").first.click()
    page.wait_for_timeout(300)
    check("미리보기 열림", page.locator("#modal").is_visible() and len(page.input_value("#modalText")) > 20)
    page.click("#modalCancel")
    page.wait_for_timeout(200)

    # 8) 백업 저장
    with page.expect_download() as dl_info:
        page.click("#exportBtn")
    dl = dl_info.value
    path = os.path.join(SHOTS, "backup_download.json")
    dl.save_as(path)
    data = json.load(open(path, encoding="utf-8"))
    check("백업 파일 저장", data.get("version") == 2 and len(data.get("items", [])) == 35,
          f"{dl.suggested_filename} · {len(data.get('items', []))}종")

    # 9) 백업 불러오기 (현재 35종 → 같은 파일)
    page.set_input_files("#importFile", path)
    page.wait_for_timeout(800)
    check("백업 불러오기 35종", page.locator(".row").count() == 35, f"rows={page.locator('.row').count()}")

    # 10) 잘못된 파일
    bad = os.path.join(SHOTS, "bad.json")
    open(bad, "w").write("{not json")
    page.set_input_files("#importFile", bad)
    page.wait_for_timeout(500)
    check("깨진 파일 오류 토스트", "읽지 못" in page.locator("#toast").inner_text())

    # 11) manifest / icon / sw
    for f in ["manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-180.png", "icon-32.png", "sw.js"]:
        r = page.request.get(f"http://127.0.0.1:{PORT}/{f}")
        check(f"HTTP 200 {f}", r.status == 200, f"status={r.status}")
    man = page.evaluate("fetch('manifest.webmanifest').then(r=>r.json())")
    check("manifest standalone", man.get("display") == "standalone" and man.get("short_name") == "재고관리",
          man.get("short_name"))
    page.wait_for_timeout(1200)
    sw = page.evaluate("navigator.serviceWorker.getRegistrations().then(a=>a.length)")
    check("서비스워커 등록", sw >= 1, f"n={sw}")

    # 12) 새로고침 후 데이터 유지
    before = page.locator(".row").count()
    page.reload(wait_until="load")
    page.wait_for_timeout(700)
    check("새로고침 유지", page.locator(".row").count() == before, f"{before}->{page.locator('.row').count()}")

    # 13) 스크린샷
    page.screenshot(path=os.path.join(SHOTS, "desktop.png"), full_page=False)
    page.screenshot(path=os.path.join(SHOTS, "desktop_full.png"), full_page=True)

    m = ctx.new_page()
    m.on("pageerror", lambda e: errors.append("mobile: " + str(e)))
    m.set_viewport_size({"width": 390, "height": 844})
    m.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load")
    m.wait_for_timeout(700)
    m.screenshot(path=os.path.join(SHOTS, "mobile.png"), full_page=False)
    m.screenshot(path=os.path.join(SHOTS, "mobile_full.png"), full_page=True)

    browser.close()

srv.shutdown()

print("\n--- 콘솔 ---")
bad_console = [c for c in console if c[0] in ("error", "warning")]
for c in console[-15:]:
    print(c)
print("errors:", errors)
print("bad console:", bad_console)
fails = [r for r in results if not r[1]]
print(f"\n결과: {len(results)-len(fails)}/{len(results)} 통과")
sys.exit(1 if (fails or errors or bad_console) else 0)
