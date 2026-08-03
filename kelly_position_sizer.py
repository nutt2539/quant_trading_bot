"""
DYNAMIC KELLY CRITERION POSITION SIZING ENGINE
Author: Quant AI Engineering Team
"""

def calculate_kelly_allocation(
    system_cash_thb: float,
    ai_sentiment_score: float = 0.20,
    win_rate: float = 0.58,
    win_loss_ratio: float = 2.20,
    base_allocation_thb: float = 20000.0,
    max_portfolio_equity: float = 100000.0
) -> dict:
    """
    Calculates optimal trade size in THB using Fractional Kelly Criterion:
    f* = Conviction * (Win_Rate - ((1 - Win_Rate) / Win_Loss_Ratio))
    
    Dynamically scales trade allocation between ฿10,000 THB and ฿30,000 THB based on AI Sentiment Conviction.
    """
    if system_cash_thb <= 0:
        return {
            "allocated_thb": 0.0,
            "kelly_pct": 0.0,
            "conviction_tier": "NO_CASH",
            "reason": "เงินสดไม่เพียงพอสำหรับการยิงออเดอร์"
        }
        
    # 1. Standard Kelly Fraction Calculation
    loss_rate = 1.0 - win_rate
    raw_kelly = win_rate - (loss_rate / win_loss_ratio)
    
    # 2. Fractional Kelly (Half-Kelly for institutional risk safety = 0.5 * raw_kelly)
    half_kelly = max(0.05, min(0.30, 0.5 * raw_kelly))
    
    # 3. AI Sentiment Conviction Multiplier (Score from -1.0 to +1.0)
    # Higher positive sentiment increases conviction
    if ai_sentiment_score >= 0.50:
        conviction_mult = 1.5  # High Conviction (Tier 1)
        conviction_tier = "🔥 HIGH CONVICTION (เกรด A+)"
    elif ai_sentiment_score >= 0.20:
        conviction_mult = 1.0  # Moderate Conviction (Tier 2)
        conviction_tier = "🟢 MODERATE CONVICTION (เกรด B+)"
    elif ai_sentiment_score >= 0.0:
        conviction_mult = 0.75 # Neutral Conviction (Tier 3)
        conviction_tier = "🟡 NEUTRAL CONVICTION (เกรด B)"
    else:
        conviction_mult = 0.50 # Low Conviction (Tier 4)
        conviction_tier = "⚠️ LOW CONVICTION (เกรด C)"
        
    # Calculate recommended THB amount
    calculated_thb = base_allocation_thb * conviction_mult
    
    # Enforce Hard Safety Limits (Min ฿10,000 THB, Max ฿30,000 THB, Max Available Cash)
    final_trade_thb = max(10000.0, min(30000.0, calculated_thb))
    final_trade_thb = min(final_trade_thb, system_cash_thb)
    
    return {
        "allocated_thb": round(final_trade_thb, 2),
        "kelly_pct": round(half_kelly * 100.0, 2),
        "conviction_multiplier": conviction_mult,
        "conviction_tier": conviction_tier,
        "reason": f"Kelly Sizing = ฿{final_trade_thb:,.2f} ({conviction_tier} | AI Score: {ai_sentiment_score:+.2f})"
    }
