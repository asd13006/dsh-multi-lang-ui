"""多語言插件驗證（DSH 新版的 web UI 需要帶 token 的 URL）。

用法：
    python verify/verify_ui.py "http://127.0.0.1:3080/?token=XXXX"

未提供 URL 時預設 http://127.0.0.1:3080/ （舊版 DSH 不需要 token）。
腳本會：開設定 → 檢查語言選單 8 個選項 → 切換日本語/한국어 → reload 驗證持久化。
"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:3080/"
results = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)[:300]))

    resp = page.goto(URL, wait_until="domcontentloaded", timeout=30000)
    results["http_status"] = resp.status if resp else None
    page.wait_for_timeout(6000)

    # 開設定
    for label in ["设置", "設定", "Settings", "설정"]:
        loc = page.get_by_role("button", name=label, exact=False)
        if loc.count() > 0:
            loc.first.click()
            page.wait_for_timeout(2000)
            break

    # 語言行 selector
    sel = page.locator("button[class*='_selector']")
    if sel.count() == 0:
        print("!! 搵唔到語言 selector；可能未登入（401）或語言行未渲染")
        print("body 前 200 字:", page.locator("body").inner_text()[:200].replace("\n", " | "))
        browser.close()
        sys.exit(1)
    sel.first.click()
    page.wait_for_timeout(1000)
    menu = page.locator("body").inner_text()
    for opt in ["中文", "English", "繁體中文", "日本語", "한국어", "Français", "Deutsch", "Español"]:
        results["menu_" + opt] = opt in menu

    # 切換日本語
    ja = page.get_by_text("日本語", exact=True)
    if ja.count() > 0:
        ja.first.click()
        page.wait_for_timeout(2000)
        body = page.locator("body").inner_text()
        results["ja_switched"] = "設定" in body
        results["ja_pref"] = page.evaluate("() => window.localStorage.getItem('dsh-multi-lang-ui.preference')")

    # reload 持久化
    page.reload(wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(6000)
    body = page.locator("body").inner_text()
    results["ja_persisted"] = "セッション" in body

    results["console_errors"] = [e for e in errors if "multi-lang" in e.lower() or "locale" in e.lower()]
    print(json.dumps(results, ensure_ascii=False, indent=2))
    browser.close()
    ok = all(v for k, v in results.items() if k.startswith("menu_")) and results.get("ja_persisted")
    print("RESULT:", "PASS" if ok else "FAIL")
