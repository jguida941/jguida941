"""Bounded, authority-backed dashboard composition CSS."""
from __future__ import annotations


def dashboard_css() -> str:
    """Return dashboard layout plus per-theme content-surface policy."""
    return """
.ps-main[data-page-orientation="delegated"] { padding-block: 36px 72px; padding-inline: 20px; }
.db-dashboard { contain: paint; display: flex; flex-direction: column; gap: var(--gap-grid); }
.db-section { background: var(--layer-01); border: 1px solid var(--section-edge); border-radius: var(--radius-panel); padding: var(--ps-pad); box-shadow: none; }
:root[data-theme="carbon"] .db-section { border: 0; }
.db-section[hidden] { display: none; }
.db-section-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.db-eyebrow { margin: 0 0 4px; color: var(--ink-dim); font-size: var(--type-eyebrow); font-weight: var(--type-eyebrow-weight); text-transform: uppercase; letter-spacing: 0; }
.db-section-title { margin: 0; color: var(--ink-strong); font-size: var(--type-title); font-weight: var(--type-title-weight); }
.db-hero-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.db-hero-copy { min-width: min(100%, 430px); }
.db-hero-title { margin: 0 0 6px; color: var(--ink-strong); font-size: var(--type-title); font-weight: 600; line-height: 1.15; }
.db-hero-intro { margin: 0 0 8px; color: var(--ink-dim); font-size: var(--type-body); line-height: 1.45; }
.db-hero-kpi { display: flex; align-items: flex-end; gap: 28px; margin-top: 30px; flex-wrap: wrap; }
.db-hero-primary { color: var(--ink-strong); font-size: var(--type-display); font-weight: var(--type-display-weight); line-height: 1; }
.db-hero-label { color: var(--ink); font-size: var(--type-body); }
.db-hero-stats { display: flex; gap: 26px; flex-wrap: wrap; }
.db-hero-stat { display: flex; flex-direction: column; }
.db-hero-stat-value { color: var(--ink-strong); font-size: var(--type-metric_lg); font-weight: var(--type-metric_lg-weight); font-variant-numeric: tabular-nums; }
.db-hero-stat-label { color: var(--ink-dim); font-size: var(--type-caption); }
.db-live { display: inline-flex; align-items: center; gap: 7px; margin-top: 14px; color: var(--ink-dim); font-size: var(--type-caption); }
.db-live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--status-success); }
.db-score-ring-row { display: flex; align-items: center; gap: 14px; margin-bottom: 14px; }
.db-score-ring { --db-progress: 0; position: relative; display: grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: conic-gradient(var(--accent) calc(var(--db-progress) * 1%), var(--group-edge) 0); }
.db-score-ring::after { position: absolute; inset: 8px; content: ""; border-radius: 50%; background: var(--layer-02); }
.db-score-ring-value { position: relative; z-index: 1; color: var(--ink-strong); font-size: var(--type-caption); }
.db-score-copy { display: flex; flex-direction: column; }
.db-score-label { color: var(--ink-strong); font-weight: 600; }
.db-score-detail { color: var(--ink-dim); font-size: var(--type-caption); }
.db-calendar-scroll,.db-rhythm-scroll { overflow-x: auto; }
.db-calendar-grid { display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 1fr); gap: 3px; min-width: max-content; }
.db-calendar-cell { display: block; width: 11px; height: 11px; border-radius: 3px; background: color-mix(in srgb, var(--hairline) 18%, transparent); }
.db-calendar-cell[data-level="1"],.db-heat-cell[data-level="1"] { background: color-mix(in srgb, var(--accent) 38%, transparent); }
.db-calendar-cell[data-level="2"],.db-heat-cell[data-level="2"] { background: color-mix(in srgb, var(--accent) 58%, transparent); }
.db-calendar-cell[data-level="3"],.db-heat-cell[data-level="3"] { background: color-mix(in srgb, var(--accent) 78%, transparent); }
.db-calendar-cell[data-level="4"],.db-heat-cell[data-level="4"] { background: var(--accent); }
.db-calendar-foot { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 16px; color: var(--ink-dim); font-size: var(--type-caption); }
.db-calendar-scale { display: inline-flex; align-items: center; gap: 3px; }
.db-language-bar { display: flex; overflow: hidden; height: 13px; border-radius: 7px; background: var(--group-edge); }
.db-language-segment { display: block; width: calc(var(--db-share) * 1%); height: 100%; background: var(--db-language-color); }
.db-language-legend { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px 16px; margin-top: 16px; }
.db-language-legend-row { display: flex; align-items: center; gap: 8px; font-size: var(--type-caption); }
.db-language-dot { width: 9px; height: 9px; flex: 0 0 auto; border-radius: 50%; background: var(--db-language-color); }
.db-language-name { color: var(--ink); }
.db-language-percent { margin-left: auto; color: var(--ink-strong); font-weight: 600; }
.db-rhythm-grid { display: grid; grid-template-columns: 30px 1fr; gap: 4px 8px; align-items: start; min-width: 460px; max-width: 560px; }
.db-heat-days { display: grid; grid-auto-rows: 16px; gap: 4px; }
.db-heat-day { color: var(--ink-dim); font-size: var(--type-caption); line-height: 16px; }
.db-heat-grid { display: grid; grid-template-columns: repeat(24, 1fr); grid-auto-rows: 16px; gap: 4px; }
.db-heat-cell { display: block; border-radius: 3px; background: color-mix(in srgb, var(--hairline) 18%, transparent); }
.db-heat-hours { grid-column: 2; display: grid; grid-template-columns: repeat(24, 1fr); margin-top: 7px; color: var(--ink-dim); font-size: var(--type-caption); }
.db-heat-hour { grid-column: var(--db-column); text-align: center; }
.db-event-mix { display: flex; flex-wrap: wrap; gap: 10px 20px; margin-top: 22px; }
.db-event-item { display: inline-flex; align-items: center; gap: 8px; color: var(--ink); font-size: var(--type-caption); }
.db-event-track { width: 52px; height: 7px; overflow: hidden; border-radius: 4px; background: var(--group-edge); }
.db-event-fill { display: block; width: calc(var(--db-progress) * 1%); height: 100%; background: var(--accent); }
.db-repository-list { display: flex; flex-direction: column; gap: 8px; }
.db-empty { margin: 0; color: var(--ink-dim); font-size: var(--type-body); }
.db-repository-row { display: flex; align-items: center; gap: 10px; min-height: 44px; padding: 12px 14px; border: 1px solid var(--group-edge); border-radius: var(--radius-tile); background: var(--layer-02); }
.db-repository-name { color: var(--ink-strong); font-size: var(--type-body); text-decoration: none; }
.db-repository-meta { margin-left: auto; color: var(--ink-dim); font-size: var(--type-caption); text-align: right; }
.db-focus-lanes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.db-focus-lane-title { margin: 0 0 10px; color: var(--ink-dim); font-size: var(--type-eyebrow); text-transform: uppercase; }
.db-focus-items { display: flex; flex-direction: column; }
.db-focus-item { padding: 8px 0; border-top: 1px solid var(--row-divider); color: var(--ink); font-size: var(--type-caption); }
.db-focus-title { display: flex; align-items: center; gap: 4px; color: var(--ink-strong); font-size: var(--type-body); }
.db-focus-detail { display: block; }
.db-icon { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }
.db-snapshot-card { margin-bottom: 20px; }
.db-pipeline-title { margin: 0 0 8px; color: var(--ink-dim); font-size: var(--type-eyebrow); text-transform: uppercase; }
.db-pipeline { display: flex; flex-wrap: wrap; gap: 8px; }
.db-status { display: inline-flex; align-items: center; gap: 7px; min-height: 44px; padding: 6px 12px; border: 1px solid var(--group-edge); border-radius: var(--radius-tile); color: var(--ink); background: var(--layer-02); font-size: var(--type-chip); }
.db-status[data-status="ok"] .db-icon { color: var(--status-success); }
.db-status[data-status="warn"] .db-icon { color: var(--status-warning); }
.db-status[data-status="bad"] .db-icon { color: var(--status-danger); }
.db-footer { text-align: center; color: var(--ink-dim); font-size: var(--type-caption); }
.db-footer a { color: var(--ink); text-decoration: none; }
:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
@media (max-width: 760px) { .db-language-legend,.db-focus-lanes { grid-template-columns: 1fr; } }
@media (max-width: 480px) { .ps-main[data-page-orientation="delegated"] { padding-block: 24px 48px; padding-inline: 12px; } .db-section-head { flex-wrap: wrap; } .db-hero-top { display: grid; } }
@media (prefers-reduced-motion: reduce) { .db-dashboard * { animation: none; transition: none; } }
@media (prefers-reduced-transparency: reduce) { .theme-switcher { -webkit-backdrop-filter: none; backdrop-filter: none; } }
""".strip()
