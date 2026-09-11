"""診斷：DSH 更新後插件狀態 — console 錯誤 + 語言選單檢查"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:3080"
logs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.on("console", lambda m: logs.append((m.type, m.text[:300])))
    page.on("pageerror", lambda e: logs.append(("pageerror", str(e)[:400])))
    page.on("requestfailed", lambda r: logs.append(("reqfail", r.url[:150])))

    resp = page.goto(BASE, wait_until="domcontentloaded", timeout=30000)
    print("HTTP status:", resp.status if resp else "?")
    page.wait_for_timeout(6000)
    body = page.locator("body").inner_text()
    print("body 前 200 字:", body[:200].replace("\n", " | "))

    # 開設定睇語言行
    for label in ["设置", "設定", "Settings", "설정"]:
        loc = page.get_by_role("button", name=label, exact=False)
        if loc.count() > 0:
            loc.first.click()
            print("clicked settings:", label)
            page.wait_for_timeout(1500)
            break
    menu_btn = page.locator('button[aria-haspopup="menu"]')
    print("aria-haspopup=menu 按鈕數:", menu_btn.count())
    if menu_btn.count() > 0:
        try:
            print("第一個 menu 按鈕文字:", repr(menu_btn.first.inner_text()[:40]))
            menu_btn.first.click()
            page.wait_for_timeout(800)
            m = page.locator("body").inner_text()
            for opt in ["中文", "English", "繁體中文", "日本語", "한국어", "Français", "Deutsch", "Español"]:
                print(f"  選項 {opt}:", opt in m)
        except Exception as e:
            print("menu err:", e)

    print("\n=== console 相關日誌 ===")
    for t, text in logs:
        if any(k in text.lower() for k in ["multi-lang", "locale", "error", "fail", "cannot", "undefined"]):
            print(f"[{t}] {text}")
    print("\n=== requestfailed ===")
    for t, text in logs:
        if t == "reqfail":
            print(text)
    browser.close()
    print("DONE")
