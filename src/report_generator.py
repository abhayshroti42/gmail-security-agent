"""
report_generator.py
----------------------
Builds a local, self-contained HTML "Email Security Report" for one
analyzed email, using ONLY data already produced by
run_email_security_agent() (Day 7) - no new analysis, no extra Gemini
calls, no network access, no database, no external resources.

Visual design: a dark navy/blue security-dashboard aesthetic. Status
colors (SPAM=red, SUSPICIOUS=amber, SAFE=green) are used consistently
and ONLY for those three states - everything else uses the neutral
navy/blue/white palette.

DISPLAY-MAPPING FIX: when the AI layer is unavailable, the header badge
no longer shows a meaningless "UNKNOWN" - it derives a SAFE/SUSPICIOUS/
SPAM label from the ML prediction + deterministic risk level that are
already present in the decision dict. This changes ONLY what is shown,
not any classification/risk logic - _resolve_display_status() reads
existing fields, it does not compute new ones.

No internal/debug details (message IDs, filenames, raw state, raw
exceptions, API error codes, quota info, model names) are ever shown.
"""

import html
import os

_REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports"
)

# ---------------------------------------------------------------------------
# Palette: dark navy/blue product theme + three status colors used ONLY
# for their corresponding classification, consistently throughout.
# ---------------------------------------------------------------------------

_NAVY = "#0b1220"
_NAVY_SOFT = "#111b2e"
_BLUE = "#2563eb"
_BLUE_SOFT = "#eff4ff"
_INK = "#0f172a"
_MUTED = "#64748b"
_BORDER = "#e6e9ef"
_BG = "#f4f6fa"

_STATUS = {
    "SPAM": {"color": "#b91c1c", "bg": "#fdecec", "label": "SPAM DETECTED",
              "icon": "alert"},
    "SUSPICIOUS": {"color": "#b45309", "bg": "#fff6e5", "label": "SUSPICIOUS",
                    "icon": "alert"},
    "SAFE": {"color": "#15803d", "bg": "#eaf7ee", "label": "SAFE", "icon": "check"},
}

_RISK_COLORS = {"LOW": "#15803d", "MEDIUM": "#b45309", "HIGH": "#b91c1c"}
_RISK_DEFAULT = "#64748b"

_LLM_FAILURE_MARKERS = [
    "llm call failed", "429", "resource_exhausted", "quota", "could not parse",
]


def _escape(value) -> str:
    return html.escape(str(value)) if value is not None else ""


def _resolve_display_status(decision: dict) -> str:
    """
    Return one of "SPAM", "SUSPICIOUS", "SAFE" for display purposes.

    If the AI produced a real classification, use it as-is. Otherwise
    (AI unavailable / any other value), derive a display label from the
    ML prediction and deterministic risk level ALREADY present in
    `decision` - this is a read of existing evidence, not new analysis.
    """
    classification = decision.get("classification", "")
    if classification in _STATUS:
        return classification

    ml_prediction = str(decision.get("ml_prediction", "")).upper()
    risk = str(decision.get("risk", "")).upper()

    if ml_prediction == "SPAM":
        return "SPAM"
    if risk == "HIGH":
        return "SUSPICIOUS"
    if risk == "MEDIUM":
        return "SUSPICIOUS"
    return "SAFE"


def _risk_color(risk: str) -> str:
    return _RISK_COLORS.get(str(risk).upper(), _RISK_DEFAULT)


def _llm_assessment_unavailable(decision: dict) -> bool:
    if decision.get("classification") == "UNAVAILABLE":
        return True
    assessment_text = str(decision.get("assessment", "")).lower()
    return any(marker in assessment_text for marker in _LLM_FAILURE_MARKERS)


# ---------------------------------------------------------------------------
# Small inline outline-style icons (no external resources). currentColor
# lets each icon inherit its container's color.
# ---------------------------------------------------------------------------

_ICONS = {
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M12 3l7 3v6c0 4.5-3 7.7-7 9-4-1.3-7-4.5-7-9V6l7-3z"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 7L10 18l-5-5"/></svg>',
    "alert": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 3l10 18H2L12 3z"/><path d="M12 9v5"/><circle cx="12" cy="17" r="0.6" fill="currentColor" stroke="none"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>',
    "link": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M10 14a4 4 0 005.7 0l2.6-2.6a4 4 0 10-5.6-5.6L11.3 7"/><path d="M14 10a4 4 0 00-5.7 0L5.7 12.6a4 4 0 105.6 5.6L12.7 17"/></svg>',
    "brain": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="12" r="8"/><path d="M8 12h8M12 8v8"/></svg>',
    "circle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="8"/></svg>',
}


def _icon(name: str) -> str:
    return f'<span class="icon">{_ICONS.get(name, "")}</span>'


def _chip_list(items):
    if not items:
        return ""
    return "".join(f'<span class="chip">{_escape(i)}</span>' for i in items)


def _threat_row(label: str, items: list, icon: str, count_label: str = None) -> str:
    found = bool(items)
    row_class = "threat-found" if found else "threat-clear"
    status_icon = "alert" if found else "check"
    body = _chip_list(items) if found else '<span class="muted">None detected</span>'
    suffix = f" &middot; {_escape(count_label)}" if count_label else ""
    return f"""
        <div class="threat-row {row_class}">
          <div class="threat-icon">{_icon(status_icon)}</div>
          <div class="threat-body">
            <div class="threat-label">{_icon(icon)}<span>{_escape(label)}{suffix}</span></div>
            <div class="threat-findings">{body}</div>
          </div>
        </div>"""


def _ai_status_panel_html() -> str:
    return f"""
      <div class="ai-status-panel">
        <div class="ai-status-head">
          {_icon("brain")}
          <div>
            <div class="ai-status-title">AI Analysis Status</div>
            <div class="ai-status-subtitle">AI-assisted analysis temporarily unavailable</div>
          </div>
        </div>
        <div class="ai-status-heading">Security analysis remains active</div>
        <ul class="ai-status-list">
          <li><span class="dot dot-ok">{_icon('check')}</span> ML Spam Classifier</li>
          <li><span class="dot dot-ok">{_icon('check')}</span> Deterministic Security Analysis</li>
          <li><span class="dot dot-ok">{_icon('check')}</span> Link/Threat Signal Analysis</li>
          <li><span class="dot dot-pending">{_icon('circle')}</span> Gemini AI Assessment &mdash; temporarily unavailable</li>
        </ul>
        <div class="ai-status-note">
          The security decision is still supported by the local ML classifier
          and deterministic security analysis.
        </div>
      </div>"""


def _ai_assessment_section_html(decision: dict) -> str:
    if _llm_assessment_unavailable(decision):
        return _ai_status_panel_html()

    assessment = _escape(decision.get("assessment", "No assessment available."))
    key_risk_signals = decision.get("key_risk_signals", [])
    key_signals_html = (
        _chip_list(key_risk_signals)
        if key_risk_signals
        else '<span class="muted">No specific signals flagged by the AI assessment.</span>'
    )
    return f"""
      <div class="assessment-box">
        <div class="assessment-heading">{_icon('brain')}<span>Gemini / LangGraph Assessment</span></div>
        <p class="assessment-text">{assessment}</p>
        <div class="assessment-signals-label">Key Risk Signals</div>
        <div>{key_signals_html}</div>
      </div>"""


def build_report(msg_id: str, email_data: dict, decision: dict, security_analysis: dict) -> str:
    """
    Write an HTML security-dashboard report for one email and return its
    absolute file path. Function signature and return value are unchanged.
    """
    os.makedirs(_REPORTS_DIR, exist_ok=True)

    display_status = _resolve_display_status(decision)
    status = _STATUS[display_status]
    risk = decision.get("risk", "UNKNOWN")
    risk_color = _risk_color(risk)
    signals = security_analysis.get("risk_signals", {})
    ml_confidence = decision.get("ml_confidence", 0) or 0

    sender = _escape(email_data.get("sender", ""))
    domain = _escape(security_analysis.get("sender_domain", "(unknown)"))
    subject = _escape(email_data.get("subject", "") or "(no subject)")
    date_value = email_data.get("date")
    body_preview = _escape(security_analysis.get("body_preview", ""))
    ml_prediction = _escape(decision.get("ml_prediction", "UNKNOWN"))

    date_row_html = ""
    if date_value:
        date_row_html = f"""
              <div class="detail-row">
                <div class="detail-label">Date</div>
                <div class="detail-value">{_escape(date_value)}</div>
              </div>"""

    ai_assessment_section = _ai_assessment_section_html(decision)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Email Security Report - {_escape(display_status)}</title>
<style>
  :root {{
    --navy: {_NAVY}; --navy-soft: {_NAVY_SOFT}; --blue: {_BLUE}; --blue-soft: {_BLUE_SOFT};
    --ink: {_INK}; --muted: {_MUTED}; --border: {_BORDER}; --bg: {_BG};
    --status: {status['color']}; --status-bg: {status['bg']}; --risk: {risk_color};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', Roboto, -apple-system, Arial, sans-serif;
    background: var(--bg); margin: 0; padding: 28px 16px; color: var(--ink);
    -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 860px; margin: 0 auto; }}
  .icon svg {{ width: 16px; height: 16px; display: block; }}

  /* Header */
  .header {{
    background: linear-gradient(160deg, var(--navy) 0%, var(--navy-soft) 100%);
    border-radius: 16px; padding: 30px 34px; color: #fff;
    box-shadow: 0 8px 24px rgba(11,18,32,0.25);
  }}
  .header-brand {{
    display: flex; align-items: center; gap: 8px; color: #93c5fd;
    font-size: 12px; text-transform: uppercase; letter-spacing: 1.6px;
    font-weight: 600; margin-bottom: 22px;
  }}
  .header-brand .icon svg {{ width: 15px; height: 15px; }}
  .status-row {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }}
  .status-badge {{
    display: inline-flex; align-items: center; gap: 10px;
    background: var(--status-bg); color: var(--status);
    padding: 10px 20px; border-radius: 10px;
    font-size: 20px; font-weight: 800; letter-spacing: 0.3px;
  }}
  .status-badge .icon svg {{ width: 20px; height: 20px; }}
  .risk-block {{ text-align: right; }}
  .risk-block .risk-label {{
    font-size: 11px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8; margin-bottom: 4px;
  }}
  .risk-value {{
    display: inline-block; font-weight: 700; font-size: 14px; color: #fff;
    background: var(--risk); padding: 4px 14px; border-radius: 999px;
  }}

  /* Panel body */
  .panel {{ background: #fff; margin-top: 14px; border-radius: 16px; border: 1px solid var(--border);
            box-shadow: 0 1px 2px rgba(15,23,42,0.03); overflow: hidden; }}

  .summary-grid {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 1px; background: var(--border);
  }}
  .summary-card {{ background: #fff; padding: 18px 20px; transition: background 0.15s ease; }}
  .summary-card:hover {{ background: #fafbfd; }}
  .summary-card .label {{
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); margin-bottom: 6px;
  }}
  .summary-card .value {{ font-size: 19px; font-weight: 700; color: var(--ink); }}

  .section {{ padding: 26px 32px; border-top: 1px solid var(--border); }}
  .section-title {{
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.7px;
    color: var(--navy); margin-bottom: 18px;
  }}
  .section-title .icon {{ color: var(--blue); }}

  .detail-row {{ display: flex; padding: 9px 0; border-bottom: 1px solid #f1f3f7; font-size: 14px; }}
  .detail-row:last-child {{ border-bottom: none; }}
  .detail-label {{ width: 150px; flex-shrink: 0; color: var(--muted); font-weight: 600; }}
  .detail-value {{ color: var(--ink); word-break: break-word; }}

  .threat-row {{ display: flex; gap: 14px; padding: 14px 16px; border-radius: 12px; margin-bottom: 10px;
                 border: 1px solid transparent; transition: box-shadow 0.15s ease; }}
  .threat-row:hover {{ box-shadow: 0 2px 8px rgba(15,23,42,0.06); }}
  .threat-row.threat-found {{ background: #fdf3f2; border-color: #f6dedb; }}
  .threat-row.threat-clear {{ background: #f4faf6; border-color: #dcefe1; }}
  .threat-row.threat-found .threat-icon {{ color: #b91c1c; }}
  .threat-row.threat-clear .threat-icon {{ color: #15803d; }}
  .threat-icon .icon svg {{ width: 18px; height: 18px; }}
  .threat-label {{ display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 13px; color: var(--ink); margin-bottom: 6px; }}
  .threat-label .icon {{ color: var(--blue); }}

  .chip {{
    display: inline-block; background: #fff; border: 1px solid var(--border);
    padding: 3px 11px; border-radius: 999px; font-size: 12px; margin: 2px 4px 2px 0; color: var(--ink);
  }}
  .muted {{ color: var(--muted); font-size: 13px; font-style: italic; }}

  .assessment-box {{
    background: var(--blue-soft); border-left: 4px solid var(--blue); border-radius: 10px; padding: 18px 22px;
  }}
  .assessment-heading {{ display: flex; align-items: center; gap: 8px; font-size: 11px; text-transform: uppercase;
                          letter-spacing: 0.8px; color: var(--blue); font-weight: 700; margin-bottom: 10px; }}
  .assessment-text {{ font-size: 14px; line-height: 1.65; color: var(--ink); margin: 0 0 14px 0; }}
  .assessment-signals-label {{ font-size: 12px; font-weight: 700; color: var(--muted); margin-bottom: 6px; }}

  .ai-status-panel {{
    background: #f8fafc; border: 1px solid var(--border); border-left: 4px solid #94a3b8;
    border-radius: 10px; padding: 20px 24px;
  }}
  .ai-status-head {{ display: flex; align-items: center; gap: 12px; margin-bottom: 16px; color: #64748b; }}
  .ai-status-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; }}
  .ai-status-subtitle {{ font-size: 16px; font-weight: 700; color: var(--ink); margin-top: 2px; }}
  .ai-status-heading {{ font-size: 13px; font-weight: 600; color: var(--ink); margin-bottom: 10px; }}
  .ai-status-list {{ list-style: none; padding: 0; margin: 0 0 16px 0; font-size: 14px; }}
  .ai-status-list li {{ display: flex; align-items: center; gap: 10px; padding: 5px 0; color: var(--ink); }}
  .dot-ok {{ color: #15803d; }}
  .dot-pending {{ color: #94a3b8; }}
  .ai-status-note {{
    font-size: 13px; color: var(--muted); line-height: 1.6; border-top: 1px solid var(--border); padding-top: 12px;
  }}

  .body-preview {{
    background: #fbfbfc; border: 1px solid var(--border); border-radius: 10px; padding: 16px;
    font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; white-space: pre-wrap;
    word-break: break-word; color: #334155; max-height: 260px; overflow-y: auto;
  }}

  .footer {{ text-align: center; padding: 22px; font-size: 12px; color: var(--muted); }}

  @media (max-width: 560px) {{
    .header {{ padding: 22px 20px; border-radius: 12px; }}
    .status-row {{ flex-direction: column; align-items: flex-start; }}
    .risk-block {{ text-align: left; }}
    .section {{ padding: 20px 20px; }}
    .detail-row {{ flex-direction: column; gap: 2px; }}
    .detail-label {{ width: auto; }}
  }}
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="header-brand">{_icon('shield')}<span>Email Security Report</span></div>
      <div class="status-row">
        <div class="status-badge">{_icon(status['icon'])}<span>{status['label']}</span></div>
        <div class="risk-block">
          <div class="risk-label">Risk Level</div>
          <div class="risk-value">{_escape(risk)}</div>
        </div>
      </div>
    </div>

    <div class="panel">
      <div class="summary-grid">
        <div class="summary-card"><div class="label">ML Prediction</div><div class="value">{ml_prediction}</div></div>
        <div class="summary-card"><div class="label">ML Confidence</div><div class="value">{ml_confidence:.1f}%</div></div>
        <div class="summary-card"><div class="label">Risk Level</div><div class="value">{_escape(risk)}</div></div>
        <div class="summary-card"><div class="label">Overall Status</div><div class="value">{status['label']}</div></div>
      </div>

      <div class="section">
        <div class="section-title">{_icon('mail')}<span>Email Details</span></div>
        <div class="detail-row"><div class="detail-label">Sender</div><div class="detail-value">{sender}</div></div>
        <div class="detail-row"><div class="detail-label">Sender Domain</div><div class="detail-value">{domain}</div></div>
        <div class="detail-row"><div class="detail-label">Subject</div><div class="detail-value">{subject}</div></div>
        {date_row_html}
      </div>

      <div class="section">
        <div class="section-title">{_icon('link')}<span>Threat Analysis</span></div>
        {_threat_row("Suspicious Keywords", signals.get('suspicious_keywords_found', []), "alert")}
        {_threat_row("Urgency Language", signals.get('urgency_language_found', []), "alert")}
        {_threat_row("Suspicious Links", signals.get('suspicious_links', []), "link", count_label=f"{signals.get('link_count', 0)} link(s) total")}
      </div>

      <div class="section">
        <div class="section-title">{_icon('brain')}<span>AI Security Assessment</span></div>
        {ai_assessment_section}
      </div>

      <div class="section">
        <div class="section-title">{_icon('mail')}<span>Email Preview</span></div>
        <div class="body-preview">{body_preview}</div>
      </div>
    </div>

    <div class="footer">Generated locally by the Email Security Agent &middot; No data leaves your machine</div>
  </div>
</body>
</html>"""

    safe_msg_id = "".join(c for c in msg_id if c.isalnum())
    report_path = os.path.join(_REPORTS_DIR, f"{safe_msg_id}.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return os.path.abspath(report_path)