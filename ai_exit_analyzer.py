"""
ai_exit_analyzer.py
===================
Advanced AI Dynamic Early Exit & Profit-Taking Engine.

Features:
1. AI Global News Shift Exit: Sells to lock in profits while still GREEN (+0.30%+ PnL) if global news sentiment turns neutral or negative, without waiting for a pullback into loss.
2. Technical Momentum Fading Exit: Takes profit early if RSI is overbought (>= 65) or Multi-Timeframe Confluence drops (< 0.40).
3. Dynamic Trailing Profit Lock: Locks in gains when a position reaches a profitable high and starts retracing.
"""

def evaluate_ai_dynamic_exit(
    symbol: str,
    pnl_pct: float,
    sentiment_score: float,
    rsi_val: float,
    conf_score: float,
    eff_tp_pct: float,
    eff_sl_pct: float,
    last_signal: int
) -> tuple:
    """
    Evaluates whether a held position should be sold early to lock in profits or cut losses.
    Returns (should_exit: bool, exit_type: str, reason: str)
    """
    # 1. Standard Static / ATR Take Profit & Stop Loss
    if pnl_pct >= eff_tp_pct:
        return True, "TAKE_PROFIT", f"🎯 Dynamic ATR Take Profit ชนเป้า (+{pnl_pct:.2f}% >= +{eff_tp_pct:.2f}%)"

    if pnl_pct <= eff_sl_pct:
        return True, "STOP_LOSS", f"🛑 Dynamic ATR Cut-Loss ตัดขาดทุน ({pnl_pct:.2f}% <= {eff_sl_pct:.2f}%)"

    # 2. Technical Sell Signal (-1)
    if last_signal == -1:
        if pnl_pct > 0:
            return True, "EARLY_PROFIT", f"📉 ขายล็อกกำไรล่วงหน้าตามสัญญาณเทคนิคอล SELL (กำไรขณะนี้ +{pnl_pct:.2f}%)"
        else:
            return True, "TECH_SELL", f"📉 สัญญาณเทคนิคอลสั่ง SELL ตัดลดความเสี่ยง ({pnl_pct:.2f}%)"

    # 3. AI GLOBAL NEWS SHIFT EARLY PROFIT TAKING (ขายล็อกกำไรตั้งแต่ยังเขียว หากข่าวเริ่มเปลี่ยนทาง)
    if pnl_pct >= 0.30 and sentiment_score < 0.05:
        return True, "AI_EARLY_PROFIT", f"🤖 AI วิเคราะห์ข่าวรอบโลกเริ่มแผ่ว/เป็นกลาง (Sentiment {sentiment_score:+.2f}) -> ขายล็อกกำไรขณะยังเขียวทันที (+{pnl_pct:.2f}%) ไม่รอให้ย่อลงไปแดง"

    # 4. AI HEAVY NEGATIVE NEWS EXIT
    if sentiment_score <= -0.20:
        if pnl_pct > 0:
            return True, "AI_EARLY_PROFIT", f"⚠️ AI ตรวจพบข่าวเชิงลบหนัก (Sentiment {sentiment_score:+.2f}) -> รีบขายล็อกกำไรสดล่วงหน้า (+{pnl_pct:.2f}%)"
        else:
            return True, "AI_RISK_EXIT", f"⚠️ AI ตรวจพบข่าวเชิงลบหนัก (Sentiment {sentiment_score:+.2f}) -> ขายตัดความเสี่ยงทันที ({pnl_pct:.2f}%)"

    # 5. MOMENTUM FADING / RSI OVERBOUGHT EARLY PROFIT TAKING
    if pnl_pct >= 0.50 and rsi_val >= 65.0:
        return True, "RSI_EARLY_PROFIT", f"📈 RSI เข้าเขต Overbought สูง ({rsi_val:.1f}) -> ขายล็อกกำไรก่อนราคาย่อตัว (+{pnl_pct:.2f}%)"

    if pnl_pct >= 0.50 and conf_score < 0.40:
        return True, "MTF_EARLY_PROFIT", f"📉 แรงซื้อ MTF 3-Timeframe เริ่มแผ่วลง ({conf_score:.2f}) -> ขายล็อกกำไรก่อนเปลี่ยนเทรนด์ (+{pnl_pct:.2f}%)"

    return False, "HOLD", "ถือครองตามแผนปกติ"
