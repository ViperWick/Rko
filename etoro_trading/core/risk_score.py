# -*- coding: utf-8 -*-
"""
投資組合風險評分系統
依持倉與帳戶資料計算 0-100 綜合風險分數及各維度子分數
"""
from dataclasses import dataclass
from pathlib import Path


# 高風險資產：加密貨幣（常見代碼）
CRYPTO_SYMBOLS = frozenset({
    "BTC", "ETH", "SOL", "ADA", "XRP", "DOT", "LINK", "AVAX", "MATIC",
    "UNI", "ATOM", "ALGO", "XLM", "VET", "NEAR", "FET", "HBAR", "SUI",
    "STRK", "QNT", "OKLO", "RKLB", "MSTR", "COIN", "RIOT", "CLSK",
})
# 槓桿 / 反向 ETF
LEVERAGED_ETF = frozenset({
    "TQQQ", "SQQQ", "SOXL", "SOXS", "TNA", "SPXU", "UPRO",
    "UVXY", "SDS", "QLD", "TECL", "LABU", "LABD", "FNGU", "FNGD",
})


@dataclass
class RiskDimension:
    """單一維度風險結果"""
    name: str
    score: float  # 0-100，越高越險
    detail: str
    level: str  # 低/中/高


@dataclass
class RiskScoreResult:
    """風險評分總結果"""
    overall: float  # 0-100 綜合分數
    dimensions: list[RiskDimension]
    summary: str


def _level(score: float) -> str:
    if score <= 25:
        return "低"
    if score <= 50:
        return "中"
    if score <= 75:
        return "高"
    return "很高"


def calc_risk_score(
    by_symbol: list[dict],
    cash: float,
    total_equity: float,
    total_unrealized_pnl: float = 0,
    correlation_file: Path | None = None,
) -> RiskScoreResult:
    """
    計算組合風險評分
    
    Args:
        by_symbol: 依標的彙總列表，每筆含 symbol, amount, current_value, pnl_pct
        cash: 現金餘額
        total_equity: 總淨值（現金+持倉）
        total_unrealized_pnl: 總未實現損益（可選）
        correlation_file: 相關性矩陣 CSV 路徑（可選，若有則計算相關性維度）
    """
    dimensions: list[RiskDimension] = []
    total_value = sum(r.get("current_value", r.get("amount", 0)) for r in by_symbol)
    if total_value <= 0:
        total_value = 1.0
    total_amount = sum(r.get("amount", 0) for r in by_symbol)

    # 1. 集中度風險（HHI）
    weights = [r.get("current_value", r.get("amount", 0)) / total_value for r in by_symbol if total_value > 0]
    hhi = sum(w * w for w in weights)
    # HHI: 1/N 分散時約 1/N，單一資產=1。映射到 0-100：HHI>0.1 視為高集中
    conc_score = min(100, hhi * 500)  # 0.2 -> 100
    dimensions.append(RiskDimension(
        name="集中度風險",
        score=round(conc_score, 1),
        detail=f"前 5 檔佔 {_top_n_pct(by_symbol, total_value, 5):.1f}% | HHI={hhi:.4f}",
        level=_level(conc_score),
    ))

    # 2. 波動率（用虧損分布作為代理：虧損標的占比與幅度）
    if not by_symbol:
        vol_score = 50
        vol_detail = "無持倉"
    else:
        loss_severe = sum(r.get("current_value", r.get("amount", 0)) for r in by_symbol if (r.get("pnl_pct") or 0) < -30)
        loss_moderate = sum(r.get("current_value", r.get("amount", 0)) for r in by_symbol if -30 <= (r.get("pnl_pct") or 0) < -10)
        pct_severe = (loss_severe / total_value * 100) if total_value else 0
        pct_moderate = (loss_moderate / total_value * 100) if total_value else 0
        vol_score = min(100, pct_severe * 1.5 + pct_moderate * 0.5)
        dimensions.append(RiskDimension(
            name="虧損曝險",
            score=round(vol_score, 1),
            detail=f"虧損>30% 佔 {pct_severe:.1f}% | 虧損10-30% 佔 {pct_moderate:.1f}%",
            level=_level(vol_score),
        ))

    # 3. 相關性（若有 correlation_matrix.csv）
    corr_score, corr_detail = _correlation_risk(correlation_file, by_symbol, total_value)
    if corr_score is not None:
        dimensions.append(RiskDimension(
            name="相關性風險",
            score=corr_score,
            detail=corr_detail,
            level=_level(corr_score),
        ))

    # 4. 虧損集中度（虧損部位佔組合比例）
    loss_value = sum(r.get("current_value", r.get("amount", 0)) for r in by_symbol if (r.get("pnl_pct") or 0) < -20)
    loss_pct = (loss_value / total_value * 100) if total_value else 0
    loss_conc_score = min(100, loss_pct * 2)
    dimensions.append(RiskDimension(
        name="虧損集中度",
        score=round(loss_conc_score, 1),
        detail=f"虧損>20% 部位佔組合 {loss_pct:.1f}%",
        level=_level(loss_conc_score),
    ))

    # 5. 高風險資產曝險（加密+槓桿 ETF）
    high_risk_value = 0
    for r in by_symbol:
        sym = (r.get("symbol") or "").split(" ")[0].upper()
        if sym in CRYPTO_SYMBOLS or sym in LEVERAGED_ETF:
            high_risk_value += r.get("current_value", r.get("amount", 0))
    high_risk_pct = (high_risk_value / total_value * 100) if total_value else 0
    hr_score = min(100, high_risk_pct * 2)
    dimensions.append(RiskDimension(
        name="高風險資產曝險",
        score=round(hr_score, 1),
        detail=f"加密+槓桿 ETF 佔 {high_risk_pct:.1f}%",
        level=_level(hr_score),
    ))

    # 6. 現金緩衝
    cash_pct = (cash / total_equity * 100) if total_equity else 0
    if cash_pct >= 25:
        cb_score = 10
        cb_detail = f"現金 {cash_pct:.1f}% 充足"
    elif cash_pct >= 15:
        cb_score = 30
        cb_detail = f"現金 {cash_pct:.1f}% 尚可"
    elif cash_pct >= 5:
        cb_score = 60
        cb_detail = f"現金 {cash_pct:.1f}% 偏低"
    else:
        cb_score = 90
        cb_detail = f"現金 {cash_pct:.1f}% 極低，緩衝不足"
    dimensions.append(RiskDimension(
        name="現金緩衝",
        score=cb_score,
        detail=cb_detail,
        level=_level(cb_score),
    ))

    # 綜合分數：各維度平均
    overall = sum(d.score for d in dimensions) / len(dimensions) if dimensions else 50
    summary = _level(overall) + "風險"
    if overall >= 70:
        summary += "：建議降低槓桿、增加現金、分散虧損部位"
    elif overall >= 50:
        summary += "：可考慮適度止盈、保留現金"
    else:
        summary += "：組合相對穩健"

    return RiskScoreResult(
        overall=round(overall, 1),
        dimensions=dimensions,
        summary=summary,
    )


def _top_n_pct(by_symbol: list[dict], total_value: float, n: int) -> float:
    sorted_val = sorted(
        (r.get("current_value", r.get("amount", 0)) for r in by_symbol),
        reverse=True,
    )
    top_sum = sum(sorted_val[:n])
    return (top_sum / total_value * 100) if total_value else 0


def _correlation_risk(correlation_file: Path | None, by_symbol: list[dict], total_value: float) -> tuple[float | None, str]:
    """若存在相關性 CSV，估算組合平均相關性風險（高相關=分散不足=高風險）"""
    if not correlation_file or not correlation_file.exists():
        return None, "（需執行 calc_correlation 產生 correlation_matrix.csv）"
    try:
        import csv
        lines = correlation_file.read_text(encoding="utf-8-sig").strip().split("\n")
        if len(lines) < 2:
            return None, "無相關性資料"
        reader = csv.reader(lines)
        header = next(reader)
        symbols_in_file = [h.strip() for h in header[1:] if h.strip()]
        row_data = {}
        for row in reader:
            if not row:
                continue
            key = row[0].strip()
            vals = row[1 : 1 + len(symbols_in_file)]
            row_data[key] = dict(zip(symbols_in_file, vals))
        top_symbols = [r.get("symbol", "").split(" ")[0].upper() for r in by_symbol[:15]]
        valid = [s for s in top_symbols if s in symbols_in_file and s in row_data]
        if len(valid) < 2:
            return None, "持倉標的與相關性矩陣重疊不足"
        total_corr, count = 0.0, 0
        for i, s1 in enumerate(valid[:10]):
            for s2 in valid[i + 1:]:
                try:
                    val = float(row_data.get(s1, {}).get(s2, 0) or row_data.get(s2, {}).get(s1, 0) or 0)
                    total_corr += abs(val)
                    count += 1
                except (ValueError, TypeError):
                    pass
        avg_corr = (total_corr / count) if count else 0
        score = min(100, avg_corr * 120)
        return round(score, 1), f"持倉標的重疊區平均 |r|={avg_corr:.2f}"
    except Exception:
        return None, "讀取相關性檔案失敗"
