"""Declarative report templates — data in, brand-consistent PDF out.

A template maps a structured dataset onto the Document element API. The caller
never touches a colour or font: theme + layout are encoded once, here.

Add a template by registering a builder in _REGISTRY and documenting it in the
from_template docstring. Builders return a fully populated Document.
"""

from __future__ import annotations

from collections.abc import Callable

from .document import Document
from .styles import Font, Style


def _financial_statement(data, theme=None) -> Document:
    """Build a one-page portfolio/financial statement.

    data: dict with keys
        title           : str
        subtitle        : str (optional)
        kpis            : list[dict]  (label, value, delta?)
        table           : list[list] or DataFrame  (rows of holdings/metrics)
        table_caption   : str (optional)
        right_align_cols: list[int] (optional)
        composition     : (labels, values) tuple (optional) -> donut
    """
    doc = Document(theme=theme)
    doc.add_heading(data.get("title", "Statement"), level=0)
    if data.get("subtitle"):
        doc.add_paragraph(data["subtitle"])
    if data.get("kpis"):
        doc.add_kpi_row(data["kpis"])
    if data.get("composition"):
        labels, values = data["composition"]
        doc.add_donut_chart(labels, values, title="Allocation")
    if data.get("table") is not None:
        doc.add_table(
            data["table"],
            caption=data.get("table_caption"),
            right_align_cols=data.get("right_align_cols"),
        )
    return doc


def _portfolio_risk(data, theme=None) -> Document:
    """Build a comprehensive 5-page NSE Portfolio Risk Report.

    data: dict with keys
        portfolio       : Portfolio object (name, holdings, totals)
        risk            : RiskMetrics object (volatility, sharpe, var, cvar, etc.)
        sector_data     : dict {sector: pct}
        df              : DataFrame with holdings detail (Ticker, Name, Qty, Avg Price, Current Price, P&L %, Sector)
        mc_result       : MonteCarloResult (expected_return, ci_lower, ci_upper, var_95, prob_profit, n_simulations, horizon_days)
        portfolio_cum   : pd.Series (cumulative returns for drawdown)
        recommendations : RecommendationReport (priority_actions list)
        generated_at    : datetime string
    """
    from datetime import datetime

    import pandas as pd

    doc = Document(theme=theme)
    portfolio = data.get("portfolio")
    risk = data.get("risk")
    sector_data = data.get("sector_data")
    df = data.get("df")
    mc_result = data.get("mc_result")
    portfolio_cum = data.get("portfolio_cum")
    recommendations = data.get("recommendations")
    generated_at = data.get("generated_at", datetime.now().strftime("%d %b %Y, %I:%M %p"))

    # Helper: risk assessment text
    def _risk_assessment_text(risk):
        if risk is None:
            return "Risk data not available.", "muted"
        vol = risk.volatility_annual
        sharpe = risk.sharpe
        if vol < 15 and sharpe > 1.0:
            return "LOW — low volatility with strong risk-adjusted returns.", "good"
        elif vol < 25 or sharpe > 0.5:
            return "MODERATE — moderate volatility with adequate compensation for risk taken.", "muted"
        else:
            return "HIGH — elevated volatility with weak risk-adjusted returns. Consider defensive positioning.", "bad"

    # ============================================================
    # PAGE 1 — COVER
    # ============================================================
    doc.add_heading("NSE Portfolio Risk Report", level=0)
    doc.add_paragraph(f"{portfolio.name}  •  {generated_at}", style=Style(font=Font("Inter", 13, italic=True, color=theme.muted_text), space_before=2, space_after=18))

    # KPI Row — 4 cards
    pnl_val = f"₹{portfolio.total_pnl:+,.0f}"
    pnl_pct = f"{portfolio.total_pnl_pct:+.2f}%"
    kpi_cards = [
        {"label": "Holdings", "value": str(portfolio.holding_count)},
        {"label": "Total Invested", "value": f"₹{portfolio.total_invested:,.0f}"},
        {"label": "Current Value", "value": f"₹{portfolio.total_current:,.0f}"},
        {"label": "P&L", "value": f"{pnl_val} ({pnl_pct})", "delta": pnl_pct},
    ]
    doc.add_kpi_row(kpi_cards)

    # Risk Gauge (volatility)
    if risk:
        doc.add_paragraph("Annual Volatility Gauge", style=Style(font=Font("Inter", 11, bold=True), space_before=12, space_after=6))
        # Build gauge chart
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.3, 1.3))
        ax.set_xlim(0, 80)
        ax.set_ylim(0, 1)
        ax.axis("off")
        for i in range(80):
            c = theme.good if i < 15 else theme.accent if i < 30 else theme.bad
            ax.axvspan(i, i + 1, 0, 0.55, facecolor=c, alpha=0.5, ec="none")
        val = min(risk.volatility_annual, 80)
        ax.plot([val, val], [0, 0.7], color=theme.foundation, linewidth=2, zorder=3)
        ax.plot(val, 0.7, marker="v", color=theme.foundation, markersize=5, zorder=3)
        ax.text(val, -0.35, f"{risk.volatility_annual:.1f}%", ha="center", fontsize=9, fontweight="bold", color=theme.foundation)
        ax.text(7.5, 0.65, "LOW", ha="center", fontsize=6, color=theme.good, fontweight="bold")
        ax.text(22.5, 0.65, "MOD", ha="center", fontsize=6, color=theme.accent, fontweight="bold")
        ax.text(55, 0.65, "HIGH", ha="center", fontsize=6, color=theme.bad, fontweight="bold")
        ax.set_title("Annual Volatility", fontsize=9, fontweight="bold", pad=6)
        fig.tight_layout()
        doc.add_chart(fig, space_before=6, space_after=12)

        # Risk Assessment Badge
        text, level = _risk_assessment_text(risk)
        label_color = {"good": theme.good, "muted": theme.muted_text, "bad": theme.bad}.get(level, theme.muted_text)
        doc.add_paragraph(
            f"Risk Level: {text}",
            Style(font=Font("Inter", 9, bold=True, color=label_color), space_before=4, space_after=8, alignment="center"),
        )

    doc.add_page_break()

    # ============================================================
    # PAGE 2 — EXECUTIVE SUMMARY
    # ============================================================
    doc.add_heading("1. Executive Summary", level=1)
    doc.add_paragraph("Portfolio-wide risk metrics at a glance.", style=Style(font=Font("Inter", 9), space_before=2, space_after=10))

    # Extended Metrics Table
    pnl_val = f"₹{portfolio.total_pnl:+,.0f}"
    metric_rows = [
        ("Holdings", str(portfolio.holding_count), "Total Invested", f"₹{portfolio.total_invested:,.0f}"),
        ("Current Value", f"₹{portfolio.total_current:,.0f}", "P&L", pnl_val),
        ("P&L %", f"{portfolio.total_pnl_pct:+.2f}%", "Sharpe", f"{risk.sharpe:.2f}" if risk else "N/A"),
    ]
    if risk:
        metric_rows += [
            ("Sortino", f"{risk.sortino:.2f}", "Beta", f"{risk.beta:.2f}"),
            ("Backtest CAGR", f"{risk.cagr:.1f}%", "VaR (95%)", f"{risk.var_95:.2f}%"),
            ("CVaR (95%)", f"{risk.cvar_95:.2f}%", "Volatility", f"{risk.volatility_annual:.1f}%"),
        ]
    doc.add_table(
        [["Metric", "Value", "Metric", "Value"]] + [list(r) for r in metric_rows],
        caption="Portfolio Metrics",
    )

    if risk:
        doc.add_paragraph(
            f"Annualised volatility of {risk.volatility_annual:.1f}% with a Sharpe ratio "
            f"of {risk.sharpe:.2f} indicates "
            f"{'strong' if risk.sharpe > 1 else 'adequate' if risk.sharpe > 0.5 else 'weak'} "
            f"risk-adjusted returns.",
            style=Style(font=Font("Inter", 9), space_before=12, space_after=12),
        )

    # Sector Donut + Top Holdings Bar (side by side)
    if sector_data:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # Sector donut
        labels = list(sector_data.keys())
        sizes = list(sector_data.values())
        colors = plt.cm.Set2.colors[: len(labels)]
        fig1, ax1 = plt.subplots(figsize=(3.0, 3.0))
        wedges, _texts, autotexts = ax1.pie(
            sizes,
            labels=None,
            autopct="%1.0f%%",
            startangle=90,
            colors=colors,
            textprops={"fontsize": 7},
        )
        ax1.set_title("Sector Allocation", fontsize=10, fontweight="bold")
        ax1.legend(
            wedges,
            [f"{lab} ({s:.0f}%)" for lab, s in zip(labels, sizes, strict=False)],
            loc="center left",
            bbox_to_anchor=(1, 0.5),
            fontsize=6,
        )
        fig1.tight_layout()

        # Top 10 holdings bar
        holdings = sorted(portfolio.holdings, key=lambda h: h.current_value, reverse=True)[:10]
        tickers = [h.ticker.replace(".NS", "") for h in holdings]
        total = portfolio.total_current or 1
        weights = [h.current_value / total * 100 for h in holdings]
        bar_colors = plt.cm.Set2.colors[: len(tickers)]
        fig2, ax2 = plt.subplots(figsize=(3.0, 3.0))
        bars = ax2.barh(range(len(tickers)), weights, color=bar_colors, height=0.6)
        ax2.set_yticks(range(len(tickers)))
        ax2.set_yticklabels(tickers, fontsize=7)
        ax2.set_xlabel("Weight (%)", fontsize=7)
        ax2.tick_params(axis="x", labelsize=6)
        for bar, w in zip(bars, weights, strict=False):
            ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va="center", fontsize=7)
        ax2.set_title("Top Holdings", fontsize=10, fontweight="bold")
        ax2.margins(x=0.15)
        fig2.tight_layout()

        doc.add_chart_row([fig1, fig2], space_after=12)

    doc.add_page_break()

    # ============================================================
    # PAGE 3 — RISK ANALYSIS
    # ============================================================
    doc.add_heading("2. Risk Analysis", level=1)
    doc.add_paragraph(
        "Detailed risk metrics, historical drawdown, and forward-looking simulation.",
        style=Style(font=Font("Inter", 9), space_before=2, space_after=10),
    )

    if risk:
        doc.add_table(
            [
                ["Metric", "Value", "Metric", "Value"],
                ["VaR (95%)", f"{risk.var_95:.2f}%", "CVaR (95%)", f"{risk.cvar_95:.2f}%"],
                ["Volatility", f"{risk.volatility_annual:.1f}%", "Backtest CAGR", f"{risk.cagr:.1f}%"],
                ["Max Drawdown", f"{risk.max_drawdown:.1f}%", "Total Return", f"{risk.total_return:.1f}%"],
                ["Sortino", f"{risk.sortino:.2f}", "Beta", f"{risk.beta:.2f}"],
                ["VaR (99%)", f"{risk.var_99:.2f}%", "Correlation", f"{risk.correlation_to_benchmark:.2f}"],
                ["Stock Count", str(portfolio.holding_count), "Sharpe", f"{risk.sharpe:.2f}"],
                ["Calmar Ratio", f"{risk.calmar_ratio:.2f}", "Treynor Ratio", f"{risk.treynor_ratio:.2f}"],
                ["Skewness", f"{risk.skewness:.3f}", "Excess Kurtosis", f"{risk.kurtosis_excess:.3f}"],
            ],
            caption="Risk Metrics Detail",
            right_align_cols=[1, 3],
        )

    # Drawdown Chart
    if portfolio_cum is not None and not portfolio_cum.empty:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        running_max = portfolio_cum.cummax()
        drawdown = (portfolio_cum - running_max) / running_max * 100
        fig, ax = plt.subplots(figsize=(6.3, 1.8))
        ax.fill_between(drawdown.index, drawdown.values, 0, color=theme.bad, alpha=0.2)
        ax.plot(drawdown.index, drawdown.values, color=theme.bad, linewidth=0.8)
        ax.axhline(0, color="black", linewidth=0.3)
        ax.set_title("Portfolio Drawdown", fontsize=10, fontweight="bold")
        ax.set_ylabel("Drawdown (%)", fontsize=8)
        ax.tick_params(axis="both", labelsize=7)
        fig.tight_layout()
        doc.add_chart(fig, space_before=12, space_after=12)

    # Monte Carlo Chart
    if mc_result:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6.3, 1.2))
        margin = max(abs(mc_result.ci_lower), abs(mc_result.ci_upper)) * 1.3
        margin = max(margin, 5)
        ax.set_xlim(-margin, margin)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ci_lower = max(mc_result.ci_lower, -margin)
        ci_upper = min(mc_result.ci_upper, margin)
        ax.barh(
            0.5,
            ci_upper - ci_lower,
            left=ci_lower,
            height=0.25,
            color=theme.accent,
            alpha=0.2,
            ec=theme.foundation,
            linewidth=0.5,
        )
        ax.plot(mc_result.expected_return, 0.5, "D", color=theme.foundation, markersize=5, zorder=3)
        ax.text(
            mc_result.expected_return,
            0.75,
            f"Expected: {mc_result.expected_return:.1f}%",
            ha="center",
            fontsize=7,
            color=theme.foundation,
        )
        ax.plot(mc_result.var_95, 0.25, "v", color=theme.bad, markersize=4, zorder=3)
        ax.text(
            mc_result.var_95,
            0.08,
            f"VaR 95%: {mc_result.var_95:.1f}%",
            ha="center",
            fontsize=6,
            color=theme.bad,
        )
        ax.text(
            0,
            -0.05,
            f"P(Profit): {mc_result.prob_profit:.1f}% | {mc_result.n_simulations:,} sims, "
            f"{mc_result.horizon_days}d horizon",
            ha="center",
            fontsize=6,
            color=theme.muted_text,
        )
        ax.set_title("Monte Carlo Projection", fontsize=10, fontweight="bold")
        fig.tight_layout()
        doc.add_chart(fig, space_before=12, space_after=12)

    # Priority Actions
    if recommendations and recommendations.priority_actions:
        doc.add_heading("Top Priority Actions", level=2)
        for rec in recommendations.priority_actions[:5]:
            doc.add_bullet(
                f"{rec.action.value.upper()} {rec.target}: {rec.reasoning} "
                f"({rec.urgency}, {rec.confidence:.0%} confidence)",
                style=Style(font=Font("Inter", 9), space_before=2, space_after=6),
            )

    doc.add_page_break()

    # ============================================================
    # PAGE 4 — HOLDINGS BREAKDOWN
    # ============================================================
    doc.add_heading("3. Holdings Breakdown", level=1)
    doc.add_paragraph("Per-holding P&L and detailed position data.", style=Style(font=Font("Inter", 9), space_before=2, space_after=10))

    # P&L Chart
    if df is not None and not df.empty:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        top = df.iloc[df["P&L %"].abs().argsort()[::-1][:10]] if "P&L %" in df.columns else df.head(10)
        tickers = [t.replace(".NS", "") for t in top["Ticker"]]
        pnl_values = top["P&L %"].values
        fig, ax = plt.subplots(figsize=(6.3, max(1.5, len(tickers) * 0.3)))
        colors = [theme.good if v >= 0 else theme.bad for v in pnl_values]
        bars = ax.barh(range(len(tickers)), pnl_values, color=colors, height=0.55)
        ax.set_yticks(range(len(tickers)))
        ax.set_yticklabels(tickers, fontsize=8)
        ax.axvline(0, color="black", linewidth=0.4)
        ax.set_xlabel("P&L %", fontsize=8)
        ax.tick_params(axis="x", labelsize=7)
        for bar, val in zip(bars, pnl_values, strict=False):
            px = bar.get_width()
            ax.text(
                px + (0.4 if px >= 0 else -0.4),
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}%",
                va="center",
                fontsize=7,
                ha="left" if px >= 0 else "right",
            )
        ax.set_title("Holdings P&L", fontsize=10, fontweight="bold")
        ax.margins(x=0.15)
        fig.tight_layout()
        doc.add_chart(fig, space_before=12, space_after=12)

    # Holdings Detail Table
    if df is not None and not df.empty:
        display_cols = ["Ticker", "Name", "Quantity", "Avg Price", "Current Price", "P&L %", "Sector"]
        display_df = df[display_cols].copy() if all(c in df.columns for c in display_cols) else df.copy()
        if "Name" in display_df.columns:
            display_df["Name"] = display_df["Name"].apply(lambda x: str(x)[:18] if pd.notna(x) else "")
        if "Quantity" in display_df.columns:
            display_df["Quantity"] = display_df["Quantity"].apply(lambda x: str(int(x)) if pd.notna(x) else "")
        if "P&L %" in display_df.columns:
            display_df["P&L %"] = display_df["P&L %"].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "")
        doc.add_table(
            display_df,
            caption="Holdings Detail",
            right_align_cols=[2, 3, 4, 5],
        )

    doc.add_page_break()

    # ============================================================
    # PAGE 5 — DISCLAIMER & FOOTER
    # ============================================================
    doc.add_heading("Disclaimer", level=1)
    doc.add_paragraph(
        "This report is for informational purposes only and does not "
        "constitute financial advice. Data sourced from public APIs (yfinance, NSE) "
        "may be delayed or inaccurate. Past performance is not indicative of future results. "
        "Consult a SEBI-registered advisor before making investment decisions.",
        style=Style(font=Font("Inter", 8, italic=True, color=theme.muted_text), space_before=6, space_after=8, alignment="center"),
    )
    doc.add_paragraph(
        "Generated by NSE Portfolio Risk Scanner",
        style=Style(font=Font("Inter", 8, italic=True, color=theme.muted_text), alignment="center"),
    )

    return doc


_REGISTRY: dict[str, Callable] = {
    "financial_statement": _financial_statement,
    "portfolio_risk": _portfolio_risk,
}


def build(name: str, data, **kwargs) -> Document:
    """Dispatch to a registered template builder."""
    if name not in _REGISTRY:
        raise ValueError(
            f"Unknown template '{name}'. Available: {', '.join(_REGISTRY)}"
        )
    # Theme may be passed positionally via kwargs from from_template.
    return _REGISTRY[name](data, **kwargs)