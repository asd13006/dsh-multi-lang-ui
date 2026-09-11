"""診斷（帶 token）：DSH v0.1.1 下插件狀態"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

TOKEN_URL = "http://127.0.0.1:3099/?token=4n2TUwq3EtqqVrepQ4xvh7w_kEb_t7UEtexDQQsdHyc"
logs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: logs.append((m.type, m.text[:400])))
    page.on("pageerror", lambda e: logs.append(("pageerror", str(e)[:500])))
    page.on("requestfailed", lambda r: logs.append(("reqfail", r.url[:160])))
    page.on("response", lambda r: logs.append(("http" + str(r.status), r.url[:160])) if r.status >= 400 else None)

    resp = page.goto(TOKEN_URL, wait_until="domcontentloaded", timeout=30000)
    print("token URL status:", resp.status if resp else "?")
    page.wait_for_timeout(3000)
    print("redirected URL:", page.url)
    page.wait_for_timeout(5000)
    body = page.locator("body").inner_text()
    print("body 前 150 字:", body[:150].replace("\n", " | "))

    # 開設定
    opened = False
    for label in ["设置", "設定", "Settings", "설정", "Paramètres", "Einstellungen", "Configuración"]:
        loc = page.get_by_role("button", name=label, exact=False)
        if loc.count() > 0:
            loc.first.click()
            print("clicked settings via:", label)
            page.wait_for_timeout(1500)
            opened = True
            break
    if not opened:
        print("!! 搵唔到設定按鈕")
        btns = [(b.inner_text() or "").strip() for b in page.locator("button").all()]
        print("buttons:", [t for t in btns if t][:20])

    # 語言選單
    menu_btn = page.locator('button[aria-haspopup="menu"]')
    print("aria-haspopup=menu 按鈕數:", menu_btn.count())
    if menu_btn.count() > 0:
        print("第一個:", repr(menu_btn.first.inner_text()[:40]))
        menu_btn.first.click()
        page.wait_for_timeout(900)
        m = page.locator("body").inner_text()
        for opt in ["中文", "English", "繁體中文", "日本語", "한국어", "Français", "Deutsch", "Español"]:
            print(f"  選項 {opt}:", opt in m)

    print("\n=== 插件相關 console / 錯誤 ===")
    for t, text in logs:
        low = text.lower()
        if any(k in low for k in ["multi-lang", "locale", "error", "fail", "undefined", "cannot", "not a function"]):
            print(f"[{t}] {text}")
    print("\n=== HTTP >=400 ===")
    for t, text in logs:
        if t.startswith("http"):
            print(f"[{t}] {text}")
    browser.close()
    print("DONE")
