"""Phase 7 app shell: sidebar navigation, tab panels, and the constrained
ticker/benchmark combobox component.

Design system: a "research memo" reading -- a serif display face (Fraunces)
for headings, a monospace face (IBM Plex Mono) for tickers/numbers/section
marks, and IBM Plex Sans for body copy, laid out as a persistent left
sidebar table of contents against a single active content panel. The
existing chart palette and marks in `app/dashboard/viz.py` (validated per
the `dataviz` skill, decision 0004) are left untouched -- this module only
adds page chrome around them, reusing `--series-2` (the "current portfolio"
chart accent) as the site's one signature accent color so the chart layer
and the page chrome read as one system rather than two.

Eight sections, matching `docs/project-standards.md`'s required list:
Overview, Inputs, Results, Learning, Glossary, Tools & Technologies,
References & Formulas, Real World/Corporate Applications. All eight always
render (progressive enhancement: the server marks one panel visible via the
`hidden` attribute; a small vanilla-JS layer below makes tab-switching
instant without a full page reload). Learning/Glossary/References/Real World
are placeholders here -- Phase 8 (`business-intelligence`) and Phase 9
(`educator`) fill them in; see `render_placeholder_section` for the
structure they should follow.
"""
from __future__ import annotations

import json

from app.dashboard.viz import esc

NAV_ITEMS: tuple[tuple[str, str], ...] = (
    ("overview", "Overview"),
    ("inputs", "Inputs"),
    ("results", "Results"),
    ("learning", "Learning"),
    ("glossary", "Glossary"),
    ("tools", "Tools & Technologies"),
    ("references", "References & Formulas"),
    ("real-world", "Real World / Corporate Applications"),
)

FONT_LINKS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
"""

SHELL_STYLE = """
.viz-root {
  --font-display: 'Fraunces', ui-serif, Georgia, serif;
  --font-body: 'IBM Plex Sans', system-ui, -apple-system, sans-serif;
  --font-mono: 'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
  --signal: var(--series-2);
  --signal-cool: var(--series-1);
  font-family: var(--font-body);
}
* { box-sizing: border-box; }
body { margin: 0; }
.app-shell { display: flex; align-items: flex-start; min-height: 100vh; }

/* ---- Sidebar / masthead / nav (table of contents) ---- */
.app-sidebar { flex: 0 0 264px; position: sticky; top: 0; height: 100vh; overflow-y: auto;
  padding: 26px 20px 20px; border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.masthead { display: flex; align-items: center; gap: 12px; margin-bottom: 26px; }
.masthead-mark { font-family: var(--font-mono); font-size: 13px; font-weight: 600; letter-spacing: 0.02em;
  border: 1.5px solid var(--text-primary); border-radius: 5px; width: 34px; height: 34px;
  display: flex; align-items: center; justify-content: center; flex: none; }
.masthead-title { font-family: var(--font-display); font-size: 19px; font-weight: 600; line-height: 1.15; }
.masthead-tag { font-family: var(--font-display); font-style: italic; font-size: 12px; color: var(--text-secondary); }

.app-nav { display: flex; flex-direction: column; gap: 2px; margin-bottom: auto; }
.nav-item { display: flex; align-items: baseline; gap: 10px; text-align: left; background: none; border: none;
  padding: 8px 10px; border-radius: 7px; cursor: pointer; color: var(--text-secondary); font: inherit;
  font-family: var(--font-body); font-size: 13.5px; }
.nav-item:hover { background: var(--surface-1); color: var(--text-primary); }
.nav-item .nav-mark { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); flex: none; width: 26px; }
.nav-item .nav-pending { margin-left: auto; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.04em;
  color: var(--text-muted); border: 1px solid var(--border); border-radius: 999px; padding: 1px 6px; }
.nav-item.is-active { background: var(--surface-1); color: var(--text-primary); font-weight: 600; }
.nav-item.is-active .nav-mark { color: var(--signal); }
.nav-item:focus-visible { outline: 2px solid var(--signal); outline-offset: 1px; }

.sidebar-foot { margin-top: 22px; padding-top: 16px; border-top: 1px solid var(--border); }
.sidebar-disclaimer { font-size: 11px; color: var(--text-muted); margin-top: 10px; line-height: 1.5; }

/* ---- Main content ---- */
.app-main { flex: 1 1 auto; min-width: 0; padding: 34px 28px 80px; }
.app-main-inner { max-width: 760px; margin: 0 auto; }
.tab-panel h1 { font-family: var(--font-display); font-size: 27px; font-weight: 600; margin: 0 0 4px; }
.tab-panel h2 { font-family: var(--font-display); }
.section-eyebrow { font-family: var(--font-mono); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--text-muted); margin: 0 0 8px; }
.section-lede { font-size: 14.5px; color: var(--text-secondary); max-width: 62ch; line-height: 1.6; margin: 0 0 24px; }

/* ---- Overview hero ---- */
.hero-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px;
  padding: 30px 30px 26px; margin-bottom: 22px; }
.hero-card p { font-size: 15px; line-height: 1.65; color: var(--text-secondary); max-width: 62ch; }
.hero-card p strong { color: var(--text-primary); }
.hero-cta { display: inline-flex; align-items: center; gap: 8px; background: var(--signal); color: white;
  border: none; border-radius: 7px; padding: 11px 20px; font: inherit; font-weight: 600; font-size: 14px;
  cursor: pointer; margin-top: 6px; }
.hero-cta:hover { filter: brightness(1.06); }
.method-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-top: 22px; }
.method-card { border: 1px solid var(--border); border-radius: 9px; padding: 14px 16px; background: var(--page-plane); }
.method-card .method-mark { font-family: var(--font-mono); font-size: 11px; color: var(--signal); }
.method-card h3 { font-family: var(--font-display); font-size: 15px; margin: 6px 0 4px; }
.method-card p { font-size: 12.5px; color: var(--text-secondary); margin: 0; line-height: 1.5; }
.disclaimer-strip { font-size: 12px; color: var(--text-muted); border-top: 1px solid var(--border); margin-top: 22px;
  padding-top: 14px; }

/* ---- Placeholder sections (Phase 8/9) ---- */
.placeholder-card { border: 1px dashed var(--baseline); border-radius: 12px; padding: 28px 30px; background: var(--surface-1); }
.placeholder-stamp { display: inline-block; font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.05em;
  text-transform: uppercase; color: var(--signal); border: 1px solid var(--signal); border-radius: 999px;
  padding: 3px 10px; margin-bottom: 14px; }
.placeholder-card h2 { font-size: 20px; margin: 0 0 8px; }
.placeholder-card p { font-size: 13.5px; color: var(--text-secondary); max-width: 58ch; line-height: 1.6; }
.placeholder-owner { font-family: var(--font-mono); font-size: 11.5px; color: var(--text-muted); margin-top: 16px; }

/* ---- Tools & Technologies ---- */
.tool-groups { display: flex; flex-direction: column; gap: 18px; }
.tool-group h3 { font-family: var(--font-display); font-size: 15.5px; margin: 0 0 8px; }
.tool-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.tool-list li { font-size: 13px; color: var(--text-secondary); display: flex; gap: 8px; align-items: baseline; }
.tool-list .tool-name { font-family: var(--font-mono); font-size: 12.5px; color: var(--text-primary); font-weight: 600;
  flex: none; min-width: 168px; }

/* ---- Form (Inputs section) ---- */
.form-card { background: var(--surface-1); border: 1px solid var(--border); border-radius: 12px; padding: 26px; }
.field-row { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.field { flex: 1 1 160px; display: flex; flex-direction: column; gap: 4px; }
.field label { font-size: 12px; color: var(--text-secondary); font-family: var(--font-mono); }
.field input, .field select { font: inherit; font-family: var(--font-body); padding: 8px 10px; border-radius: 6px;
  border: 1px solid var(--border); background: var(--page-plane); color: var(--text-primary); }
.holdings-label { font-family: var(--font-mono); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.04em;
  color: var(--text-secondary); margin: 20px 0 8px; }
.holding-row { display: flex; gap: 10px; align-items: flex-start; margin-bottom: 8px; }
.holding-row .field { flex: 1 1 auto; }
.holding-row input[name="weight"] { width: 100%; font-family: var(--font-mono); }
.weight-field { flex: 0 1 130px; }
.row-remove { background: transparent; border: 1px solid var(--border); border-radius: 6px; color: var(--text-muted);
  width: 34px; height: 38px; cursor: pointer; font-size: 15px; flex: none; }
.row-remove:hover { color: var(--diverging-neg); }
.add-row-btn { background: transparent; border: 1px dashed var(--baseline); border-radius: 6px;
  color: var(--text-secondary); padding: 7px 12px; font-size: 12.5px; cursor: pointer; margin-top: 2px; font: inherit; }
.submit-btn { background: var(--signal); color: white; border: none; border-radius: 7px; padding: 12px 24px;
  font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 20px; font: inherit; }
.submit-btn:hover { filter: brightness(1.06); }
.error-banner { background: color-mix(in srgb, var(--diverging-neg) 12%, var(--surface-1));
  border: 1px solid color-mix(in srgb, var(--diverging-neg) 40%, var(--border)); border-radius: 8px;
  padding: 12px 14px; font-size: 13px; color: var(--text-primary); margin-bottom: 18px; }
.form-footnote { font-size: 12px; color: var(--text-muted); margin-top: 18px; max-width: 60ch; }

/* ---- Ticker / benchmark combobox ---- */
.ticker-combobox { position: relative; }
.ticker-search { width: 100%; }
.ticker-listbox { position: absolute; z-index: 20; top: calc(100% + 4px); left: 0; right: 0; max-height: 240px;
  overflow-y: auto; margin: 0; padding: 4px; list-style: none; background: var(--surface-1);
  border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 8px 24px rgba(0,0,0,0.14); }
.ticker-option { display: flex; gap: 8px; align-items: baseline; padding: 7px 9px; border-radius: 5px; cursor: pointer;
  font-size: 13px; }
.ticker-option .opt-symbol { font-family: var(--font-mono); font-weight: 600; color: var(--text-primary); flex: none;
  min-width: 52px; }
.ticker-option .opt-name { color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ticker-option.is-active, .ticker-option:hover { background: color-mix(in srgb, var(--signal) 14%, var(--surface-1)); }
.ticker-empty-note { padding: 7px 9px; font-size: 12px; color: var(--text-muted); }

/* ---- Results freshness banner + section numbering (results panel) ---- */
.freshness-banner { background: var(--surface-1); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px 16px; font-size: 12.5px; color: var(--text-secondary); margin: 18px 0 26px; line-height: 1.6; }
.freshness-banner strong { color: var(--text-primary); font-family: var(--font-mono); font-weight: 600; font-size: 12px; }
.freshness-banner .disclaimer { font-size: 12px; color: var(--text-muted); margin-top: 8px; }
.section-title { font-family: var(--font-mono); font-size: 11.5px; text-transform: uppercase; letter-spacing: 0.05em;
  color: var(--text-muted); margin: 30px 0 12px; }
.section-title:first-of-type { margin-top: 8px; }

/* ---- Results empty state ---- */
.empty-results { border: 1px dashed var(--baseline); border-radius: 12px; padding: 32px 30px; text-align: left;
  background: var(--surface-1); }
.empty-results h2 { font-size: 19px; margin: 0 0 8px; }
.empty-results p { font-size: 13.5px; color: var(--text-secondary); max-width: 56ch; line-height: 1.6; }

@media (max-width: 860px) {
  .app-shell { flex-direction: column; }
  .app-sidebar { position: sticky; top: 0; z-index: 30; height: auto; width: 100%; flex: none;
    border-right: none; border-bottom: 1px solid var(--border); padding: 14px 16px; background: var(--page-plane); }
  .masthead { margin-bottom: 12px; }
  .app-nav { flex-direction: row; overflow-x: auto; gap: 6px; padding-bottom: 4px; margin-bottom: 0; }
  .nav-item { flex: none; white-space: nowrap; padding: 7px 10px; }
  .sidebar-foot { display: none; }
  .app-main { padding: 22px 16px 60px; }
  .method-grid { grid-template-columns: 1fr; }
}
"""


def _shell_script() -> str:
    return """
(function () {
  var buttons = document.querySelectorAll('[data-tab-target]');
  var panels = document.querySelectorAll('[data-tab-panel]');
  function activate(id, pushHash) {
    var found = false;
    panels.forEach(function (p) {
      var match = p.getAttribute('data-tab-panel') === id;
      p.hidden = !match;
      if (match) found = true;
    });
    if (!found) return;
    buttons.forEach(function (b) {
      var active = b.getAttribute('data-tab-target') === id;
      b.classList.toggle('is-active', active);
      b.setAttribute('aria-current', active ? 'true' : 'false');
    });
    if (pushHash) { history.replaceState(null, '', '#' + id); }
    var panel = document.querySelector('[data-tab-panel="' + id + '"]');
    if (panel) panel.scrollIntoView({ block: 'start' });
  }
  buttons.forEach(function (b) {
    b.addEventListener('click', function () { activate(b.getAttribute('data-tab-target'), true); });
  });
  var hash = window.location.hash.replace('#', '');
  if (hash) activate(hash, false);

  function initCombobox(root) {
    var input = root.querySelector('[data-combobox-input]');
    var hiddenField = root.querySelector('[data-combobox-value]');
    var list = root.querySelector('[data-combobox-list]');
    var source = window[root.getAttribute('data-combobox-source')] || [];
    var items = [];
    var activeIndex = -1;

    function render(query) {
      var q = query.trim().toUpperCase();
      items = !q ? [] : source.filter(function (t) {
        return t[0].indexOf(q) === 0 || t[1].toUpperCase().indexOf(q) !== -1;
      }).slice(0, 8);
      activeIndex = -1;
      list.innerHTML = '';
      if (q && items.length === 0) {
        var empty = document.createElement('li');
        empty.className = 'ticker-empty-note';
        empty.textContent = 'No match in the curated list.';
        list.appendChild(empty);
      }
      items.forEach(function (t, i) {
        var li = document.createElement('li');
        li.setAttribute('role', 'option');
        li.className = 'ticker-option';
        li.dataset.index = String(i);
        var sym = document.createElement('span'); sym.className = 'opt-symbol'; sym.textContent = t[0];
        var name = document.createElement('span'); name.className = 'opt-name'; name.textContent = t[1];
        li.appendChild(sym); li.appendChild(name);
        li.addEventListener('mousedown', function (e) { e.preventDefault(); select(i); });
        list.appendChild(li);
      });
      list.hidden = list.children.length === 0;
      input.setAttribute('aria-expanded', list.hidden ? 'false' : 'true');
    }

    function highlight(idx) {
      activeIndex = idx;
      Array.prototype.forEach.call(list.querySelectorAll('.ticker-option'), function (li, i) {
        li.classList.toggle('is-active', i === idx);
      });
    }

    function select(i) {
      var t = items[i];
      if (!t) return;
      input.value = t[0] + ' \\u2014 ' + t[1];
      hiddenField.value = t[0];
      list.hidden = true;
      input.setAttribute('aria-expanded', 'false');
    }

    input.addEventListener('input', function () { hiddenField.value = ''; render(input.value); });
    input.addEventListener('focus', function () { if (input.value) render(input.value); });
    input.addEventListener('keydown', function (e) {
      var options = list.querySelectorAll('.ticker-option');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (options.length) highlight(Math.min(activeIndex + 1, options.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (options.length) highlight(Math.max(activeIndex - 1, 0));
      } else if (e.key === 'Enter') {
        if (activeIndex >= 0) { e.preventDefault(); select(activeIndex); }
      } else if (e.key === 'Escape') {
        list.hidden = true;
      }
    });
    input.addEventListener('blur', function () {
      window.setTimeout(function () {
        if (!hiddenField.value) input.value = '';
        list.hidden = true;
      }, 120);
    });
  }

  document.querySelectorAll('[data-combobox]').forEach(initCombobox);
  window.__flInitCombobox = initCombobox;

  var addBtn = document.getElementById('add-holding-btn');
  if (addBtn) {
    addBtn.addEventListener('click', function () {
      var tpl = document.getElementById('holding-row-template');
      var frag = tpl.content.cloneNode(true);
      document.getElementById('holdings-rows').appendChild(frag);
      var rows = document.getElementById('holdings-rows').querySelectorAll('[data-combobox]');
      window.__flInitCombobox(rows[rows.length - 1]);
    });
  }
})();
"""


def render_ticker_data_script(tickers: list[tuple[str, str]], benchmarks: list[tuple[str, str]]) -> str:
    """Embed the curated universes as JSON the combobox JS filters client-side.

    `</script`-safe: JSON can't itself contain that sequence for any of our
    curated names, but the slash is escaped anyway as a defensive habit.
    """
    tickers_json = json.dumps([[s, n] for s, n in tickers], ensure_ascii=False)
    benchmarks_json = json.dumps([[s, n] for s, n in benchmarks], ensure_ascii=False)
    tickers_json = tickers_json.replace("</", "<\\/")
    benchmarks_json = benchmarks_json.replace("</", "<\\/")
    return f"<script>window.__FL_TICKERS__={tickers_json};window.__FL_BENCHMARKS__={benchmarks_json};</script>"


def render_combobox(
    *,
    field_name: str,
    source_var: str,
    selected_symbol: str = "",
    selected_label: str = "",
    placeholder: str = "Search ticker or company…",
) -> str:
    display_value = f"{selected_symbol} — {selected_label}" if selected_symbol and selected_label else ""
    return (
        f'<div class="ticker-combobox" data-combobox data-combobox-source="{esc(source_var)}">'
        f'<input type="text" class="ticker-search" data-combobox-input role="combobox" '
        f'aria-expanded="false" aria-autocomplete="list" autocomplete="off" '
        f'placeholder="{esc(placeholder)}" value="{esc(display_value)}">'
        f'<input type="hidden" name="{esc(field_name)}" data-combobox-value value="{esc(selected_symbol)}">'
        f'<ul class="ticker-listbox" role="listbox" data-combobox-list hidden></ul>'
        "</div>"
    )


def render_app_shell(*, active_tab: str, panels: dict[str, str], page_title: str, ticker_data_script: str) -> str:
    from app.dashboard import viz  # local import to avoid a cycle at module load

    nav_html = []
    for tab_id, label in NAV_ITEMS:
        pending = '<span class="nav-pending">soon</span>' if tab_id in _PENDING_TABS else ""
        active_cls = " is-active" if tab_id == active_tab else ""
        aria = "true" if tab_id == active_tab else "false"
        idx = NAV_ITEMS.index((tab_id, label)) + 1
        nav_html.append(
            f'<button type="button" class="nav-item{active_cls}" data-tab-target="{esc(tab_id)}" '
            f'aria-current="{aria}"><span class="nav-mark">§{idx:02d}</span>'
            f'<span class="nav-label">{esc(label)}</span>{pending}</button>'
        )

    panel_html = []
    for tab_id, _label in NAV_ITEMS:
        content = panels.get(tab_id, "")
        hidden_attr = "" if tab_id == active_tab else " hidden"
        panel_html.append(
            f'<section class="tab-panel" data-tab-panel="{esc(tab_id)}"{hidden_attr}>'
            f'<div class="app-main-inner">{content}</div></section>'
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(page_title)}</title>
{FONT_LINKS}
<style>{viz.CHART_STYLE}{SHELL_STYLE}</style>
</head>
<body class="viz-root">
<div class="app-shell">
  <aside class="app-sidebar">
    <div class="masthead">
      <div class="masthead-mark">FL</div>
      <div>
        <div class="masthead-title">Factor Lens</div>
        <div class="masthead-tag">Portfolio Attribution Memo</div>
      </div>
    </div>
    <nav class="app-nav" aria-label="Report sections">{''.join(nav_html)}</nav>
    <div class="sidebar-foot">
      <button class="theme-btn" type="button" data-theme-toggle>Toggle theme</button>
      <div class="sidebar-disclaimer">Internal decision-support analytics. Not investment advice, not a
      recommendation to buy, sell, or rebalance.</div>
    </div>
  </aside>
  <main class="app-main">{''.join(panel_html)}</main>
</div>
{ticker_data_script}
<script>{viz.CHART_SCRIPT}</script>
<script>{_shell_script()}</script>
</body>
</html>"""


_PENDING_TABS = {"learning", "glossary", "references", "real-world"}


# ---------------------------------------------------------------------------
# Static section content
# ---------------------------------------------------------------------------


def render_overview_section() -> str:
    return """
<div class="section-eyebrow">§01 · Overview</div>
<h1>Factor Lens</h1>
<div class="hero-card">
  <p><strong>Factor Lens explains why a portfolio behaves the way it does.</strong> Enter your holdings and
  a benchmark, and it computes your CAPM market beta, Fama-French factor loadings (size, value, and
  optionally profitability/investment), and where your portfolio sits on a modeled Markowitz efficient
  frontier &mdash; all from live market data, with the statistical diagnostics (confidence intervals,
  t-stats, p-values) shown alongside every estimate rather than a bare number.</p>
  <p>This is decision-support analytics for retail investors and small RIAs who want to understand their
  exposures, not a black-box score, a trading signal, or personalized investment advice.</p>
  <button type="button" class="hero-cta" data-tab-target="inputs">Enter your holdings →</button>
  <div class="method-grid">
    <div class="method-card">
      <div class="method-mark">CAPM</div>
      <h3>Market beta</h3>
      <p>Single-factor exposure to your chosen benchmark, with confidence intervals and significance.</p>
    </div>
    <div class="method-card">
      <div class="method-mark">Fama-French</div>
      <h3>Factor loadings</h3>
      <p>3- or 5-factor exposure (market, size, value, and optionally profitability/investment).</p>
    </div>
    <div class="method-card">
      <div class="method-mark">Markowitz</div>
      <h3>Efficient frontier</h3>
      <p>Where your as-entered portfolio sits against the modeled long-only efficient set.</p>
    </div>
  </div>
</div>
<div class="disclaimer-strip">Computed live from OpenBB (yfinance provider) equity/benchmark prices and
Kenneth French's Data Library factor series &mdash; see Tools &amp; Technologies for the full stack, and
References &amp; Formulas for the exact math once Phase 8 publishes it.</div>
"""


def render_tools_section() -> str:
    def group(title: str, items: list[tuple[str, str]]) -> str:
        rows = "".join(f'<li><span class="tool-name">{esc(n)}</span><span>{esc(d)}</span></li>' for n, d in items)
        return f'<div class="tool-group"><h3>{esc(title)}</h3><ul class="tool-list">{rows}</ul></div>'

    body = "".join(
        [
            group(
                "Application & API",
                [
                    ("Python 3.11", "language runtime"),
                    ("FastAPI", "HTTP layer for the JSON API and the server-rendered dashboard"),
                    ("Pydantic v2", "request/response schema validation, holdings/portfolio contracts"),
                    ("uv", "dependency management and lockfile (`uv.lock`)"),
                ],
            ),
            group(
                "Market & factor data",
                [
                    ("OpenBB Open Data Platform", "equity and benchmark price history (yfinance provider)"),
                    ("Kenneth French's Data Library", "Fama-French 3-/5-factor and risk-free return series, via pandas-datareader"),
                ],
            ),
            group(
                "Quantitative core",
                [
                    ("NumPy / pandas", "return-series alignment and array math"),
                    ("statsmodels", "OLS regression with Newey-West HAC standard errors (CAPM, Fama-French)"),
                    ("SciPy (SLSQP)", "constrained optimization for the long-only Markowitz efficient frontier"),
                ],
            ),
            group(
                "Presentation",
                [
                    ("Hand-built inline SVG", "every chart, no client-side charting library (see decision 0004)"),
                    ("Vanilla JavaScript", "tab navigation, the ticker combobox, theme toggle &mdash; no framework or build step"),
                    ("Server-rendered HTML/CSS", "no Jinja2; pages assembled as plain Python string templates"),
                ],
            ),
            group(
                "Quality & delivery",
                [
                    ("pytest + httpx", "live, non-mocked end-to-end tests against real market data"),
                    ("Railway", "planned deployment target (Phase 11)"),
                ],
            ),
        ]
    )
    return f"""
<div class="section-eyebrow">§06 · Tools &amp; Technologies</div>
<h1>What this was actually built with</h1>
<p class="section-lede">Named and specific, not "some data tools" &mdash; this section doubles as a record
of the real stack behind the analysis.</p>
<div class="tool-groups">{body}</div>
"""


def render_placeholder_section(*, tab_id: str, title: str, phase_label: str, owner: str, body: str) -> str:
    idx = [i for i, (t, _l) in enumerate(NAV_ITEMS, start=1) if t == tab_id][0]
    return f"""
<div class="section-eyebrow">§{idx:02d} · {esc(title)}</div>
<div class="placeholder-card">
  <span class="placeholder-stamp">Coming in {esc(phase_label)}</span>
  <h2>{esc(title)}</h2>
  <p>{body}</p>
  <div class="placeholder-owner">Owner: {esc(owner)}</div>
</div>
"""
