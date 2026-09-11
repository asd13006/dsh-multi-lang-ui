# dsh-multi-lang-ui

**Languages:** [English](README.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Español](README.es.md)

A DSH plugin that adds **multiple languages** to the [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) Web UI language options — **繁體中文, 日本語, 한국어, Français, Deutsch, Español**. Known UI strings use hand-polished translations (each language translated from the English baseline); any *new / updated / third-party* strings fall back to English (or, for 繁體中文, a runtime Simplified→Traditional converter) — so upstream UI updates and other plugins are covered **without re-translating every language**.

## Features

- Adds **6 languages** to the "Settings → General → Language" menu (alongside the built-in 中文 / English): 繁體中文, 日本語, 한국어, Français, Deutsch, Español.
- **Hand-polished translations per language**: every official locale namespace is translated string-by-string from the **English baseline** (700+ strings per language).
- **Fallback for untranslated strings**: upstream-added or third-party-plugin strings — 繁體中文 uses a built-in Simplified→Traditional char table (720+ chars) converted on the fly; the other languages fall back to English (the official `en` dictionaries are complete for every namespace), so no garbled or missing text appears.
- **DOM-level fallback conversion (zh-TW only)**: non-dictionary content (e.g. plugin-market descriptions) is converted from Simplified to Traditional via MutationObserver in zh-TW mode (inputs, code blocks and other user content are always excluded).
- **Persistence**: the language choice is stored in browser `localStorage` and survives reloads.
- **Zero-intrusion**: a pure client plugin — no upstream packages are modified; it silently degrades if the locale service is unavailable, without affecting other plugins.

## Installation

**Recommended: install from GitHub (give this link to an agent, or run it yourself)**

```bash
dsh plugin --profile web add https://github.com/asd13006/dsh-multi-lang-ui
```

Or let an agent install it: paste this repository link into DSH and ask the agent to run the command above.

After installation, restart `dsh web`, then pick your language in "Settings → General → Language".

**Removal (important)**: always use `dsh plugin remove` — it cleans up the profile's bundle list; manually deleting the package can leave dangling references that prevent DSH from starting:

```bash
dsh plugin --profile web remove dsh-multi-lang-ui
```

**npm install (once published)**:

```bash
dsh plugin --profile web add dsh-multi-lang-ui
```

## How it works

```
locale translate(ns, key)
        │
        ├─ active is one of our languages ?
        │     ├─ curated translation exists (DICTS) ?  → return it
        │     └─ missing (new strings / third-party plugins)
        │           ├─ zh-TW  → convert the zh value via the char table
        │           └─ others → fall back to the en value
        └─ other languages → handled by dsh-client-locale as usual
```

At startup the plugin:

1. Registers the per-language dictionaries for every locale namespace;
2. Wraps `locale.translate` (curated → fallback) and `locale.setLocale` (accepts our language ids, writes `localStorage`);
3. Adds all our languages to the language-options list (patches the locale snapshot and fires `locale/change` to refresh the settings row);
4. Wraps `locale.adopt` — the built-in locale's host preference loads asynchronously and resets `active` to `locale.preference ?? browser language`; if the user's preference is one of our languages, it is re-asserted;
5. Starts the DOM-level fallback conversion (MutationObserver) in zh-TW mode for non-dictionary content, restoring on switch-away.

## Do I need to re-translate after upstream updates?

**No.** Three layers of protection:

1. Upstream-added strings → covered on the fly by the fallback mechanism;
2. Upstream-changed strings → curated dictionaries keep the old values, while new/third-party strings still fall back automatically; regenerate the curated dicts when you want full sync (below);
3. To fully sync the curated translations: run the regeneration flow once — no per-string manual work.

### Regenerating the curated dictionaries (optional)

```bash
node scripts/extract.mjs <path-to-node_modules/@deepseek-ai>   # 1. extract the latest zh/en dicts into src/zh-src/ and src/en/
# 2. translate src/en/*.json → src/<lang>/*.json (LLM batch OK; keys and placeholders must match)
node scripts/assemble.mjs                                     # 3. regenerate lib/client.js
```

### Checking for uncovered Simplified characters (after upstream/third-party updates)

```bash
node scripts/collect-chars.mjs [third-party-client.js...]   # collect all Simplified characters in use
node scripts/check-missing-chars.mjs                        # list Simplified-only characters missing from the char table
```

If any are reported, add the `"简字": "繁字"` mapping to `src/zh-tw-parts/chars.json`, then run `node scripts/assemble.mjs`.

## Repository layout

```
dsh-multi-lang-ui/
├── package.json              # plugin manifest (dsh.client.inject / bundle.patch)
├── index.mjs                 # Host side: no-op entry (pure client plugin)
├── cordis.patch.yml          # Host plugin entry
├── lib/client.js             # generated browser bundle (do not edit by hand)
├── src/
│   ├── zh-src/               # extracted zh (Simplified Chinese) dicts (generated data)
│   ├── en/                   # extracted en dicts (translation baseline for all languages)
│   ├── zh-tw/ ja/ ko/ fr/ de/ es/   # per-language curated translations (quality baseline)
│   ├── zh-tw-parts/
│   │   ├── chars.json        # Simplified→Traditional char table (zh-TW runtime fallback)
│   │   ├── simplified-only.txt  # Simplified-only character checklist (maintenance)
│   │   └── collected-chars.txt  # collect-chars output
│   └── TERMINOLOGY.md        # terminology reference (used when polishing translations)
├── scripts/                  # extract / assemble / verify / collect / check
└── verify/                   # Playwright end-to-end verification scripts
```

## Known limitations

- One-to-many Simplified characters (e.g. 复 in 复制/恢复/复杂 maps to different Traditional forms) use a single mapping (復); the curated dictionaries cover the main strings, but a few new strings may convert imperfectly.
- The language preference lives in browser `localStorage` (per-browser); the built-in locale is also non-persistent for remote browsers — this is a consistent design.
- Simplified characters not in the char table pass through unchanged — run `check-missing-chars.mjs` periodically and extend the table.

## Security & privacy

- **No network traffic**: the plugin never makes any network request (no fetch / WebSocket / telemetry); the only external URL is the documentation link in this README.
- **No data collection**: no telemetry, analytics, or error reporting; the only persisted data is `localStorage["dsh-multi-lang-ui.preference"]` (a language id such as `"ja"`).
- **No access to sensitive data**: no credentials / tokens / session records / filesystem access; the host side (`index.mjs`) is a no-op.
- **Read-only DOM conversion**: only text nodes are rewritten (no innerHTML, no injection); inputs, textarea, contenteditable and code blocks (pre/code) are always excluded, so typing and code are never affected. Displayed session messages are converted (read-only display effect; stored data unchanged) and restored when switching back.
- **Zero supply-chain risk**: `dependencies` is empty — installing downloads nothing new; the client bundle is fully self-contained (zero `require`); peer dependencies are official packages already present in DSH.

## FAQ

**Q: Why doesn't dshmarket show my plugin's description?**
A: The market's description and category come from the curated "awesome-dsh-plugin" registry (`data/plugins/<owner>__<repo>.yml`), not from the local package.json. Once the entry is merged into that registry it will appear.

**Q: Do I need to publish to npm to get a version number in the market?**
A: No. The version of an installed plugin is read from its local `node_modules` package.json (a GitHub install already shows `v0.1.0`). npm publishing only affects npm search and plain-npm installs.

**Q: Do I need to update the plugin when upstream adds new strings?**
A: No — the runtime fallback covers new strings immediately, including third-party plugins' Simplified Chinese strings. Regenerate the curated dictionaries with `scripts/` when you want best-quality sync.

**Q: DSH won't start after removing the plugin?**
A: Always remove via `dsh plugin --profile web remove dsh-multi-lang-ui` (it cleans up the profile's bundle list). Manually deleting the package can leave dangling references that break startup.

**Q: After a DSH update the plugin's languages disappeared, or the page says "authentication required"?**
A: DSH 0.1.1+ added browser authentication — open the tokenized URL printed by `dsh web` in your terminal (e.g. `http://127.0.0.1:3080/?token=…`); without it the server answers 401. If the languages still don't appear, update the plugin (`dsh plugin --profile web remove dsh-multi-lang-ui`, then add it again) — plugin 0.1.1+ declares `inject: ["locale"]` and no longer depends on plugin load order.

## License

MIT
