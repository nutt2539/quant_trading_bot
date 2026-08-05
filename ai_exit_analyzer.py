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
    last_signal: int,
    fee_pct: float = 0.0
) -> tuple:
    """
    Evaluates whether a held position should be sold early, held through temporary dip, or cut loss.
    Returns (should_exit: bool, exit_type: str, reason: str)
    """
    # Net break-even PnL check for early profit taking
    min_profit_pct = fee_pct + 0.20 # Buffer of 0.20% pure profit on top of fees
    # 1. HARD CUT-LOSS BOUNDARY (ชนเกณฑ์ตัดขาดทุนสูงสุด -> กัดฟันขายเด็ดขาด 100% เพื่อปกป้องเงินต้น)
    if pnl_pct <= eff_sl_pct:
        return True, "STOP_LOSS", f"🛑 HARD CUT-LOSS: ชนเกณฑ์ Stop-Loss สูงสุด ({pnl_pct:.2f}% <= {eff_sl_pct:.2f}%) กัดฟันขายทันทีเพื่อปกป้องเงินต้น!"

    # 2. TAKE PROFIT TARGET REACHED
    if pnl_pct >= eff_tp_pct:
        return True, "TAKE_PROFIT", f"🎯 Dynamic ATR Take Profit ชนเป้ากำไร (+{pnl_pct:.2f}% >= +{eff_tp_pct:.2f}%)"

    # 3. SMART SHAKEOUT HOLD RULE (ย่อแดงชั่วคราวแต่แนวโน้มและข่าวดี -> ถือรอรีบาวด์เพื่อกำไรที่ใหญ่กว่า)
    if pnl_pct < 0 and pnl_pct > eff_sl_pct:
        if sentiment_score >= 0.15 and conf_score >= 0.45:
            return False, "HOLD_DIP", f"💡 SMART SHAKEOUT HOLD: ราคาย่อลงมาแดง ({pnl_pct:.2f}%) แต่ข่าวสารรอบโลกเชิงบวก ({sentiment_score:+.2f}) และเทรนด์ใหญ่ยังแข็งแกร่ง -> ถือรอรีบาวด์กลับมากำไรคำใหญ่"

    # 4. AI GLOBAL NEWS SHIFT EARLY PROFIT TAKING (ขายล็อกกำไรตั้งแต่ยังเขียว หากข่าวเริ่มเปลี่ยนเป็นกลาง/ลบ)
    if pnl_pct >= min_profit_pct and sentiment_score < 0.05:
        return True, "AI_EARLY_PROFIT", f"🤖 AI วิเคราะห์ข่าวรอบโลกเริ่มแผ่ว/เป็นกลาง (Sentiment {sentiment_score:+.2f}) -> ขายล็อกกำไรสุทธิหลังหักค่าธรรมเนียม (+{pnl_pct:.2f}%) ไม่รอให้ย่อลงไปแดง"

    # 5. AI HEAVY NEGATIVE NEWS EXIT
    if sentiment_score <= -0.25:
        if pnl_pct > fee_pct:
            return True, "AI_EARLY_PROFIT", f"⚠️ AI ตรวจพบข่าวเชิงลบหนัก (Sentiment {sentiment_score:+.2f}) -> ขายล็อกกำไรสุทธิหลังหักค่าธรรมเนียมทันที (+{pnl_pct:.2f}%)"
        else:
            return True, "AI_RISK_EXIT", f"⚠️ AI ตรวจพบข่าวเชิงลบหนัก (Sentiment {sentiment_score:+.2f}) -> ขายตัดความเสี่ยงทันที ({pnl_pct:.2f}%)"

    # 6. MOMENTUM FADING / RSI OVERBOUGHT EARLY PROFIT TAKING
    if pnl_pct >= (min_profit_pct + 0.30) and rsi_val >= 68.0:
        return True, "RSI_EARLY_PROFIT", f"📈 RSI เข้าเขต Overbought สูง ({rsi_val:.1f}) -> ขายล็อกกำไรก่อนราคาย่อตัว (+{pnl_pct:.2f}%)"

    if pnl_pct >= (min_profit_pct + 0.30) and conf_score < 0.35:
        return True, "MTF_EARLY_PROFIT", f"📉 แรงซื้อ MTF 3-Timeframe เริ่มแผ่วลง ({conf_score:.2f}) -> ขายล็อกกำไรก่อนเปลี่ยนเทรนด์ (+{pnl_pct:.2f}%)"

    # 7. TECHNICAL SELL SIGNAL (-1) WHEN NO BULLISH NEWS SUPPORT
    if last_signal == -1 and sentiment_score < 0.15:
        if pnl_pct > fee_pct:
            return True, "EARLY_PROFIT", f"📉 ขายล็อกกำไรสุทธิหลังหักค่าธรรมเนียมตามสัญญาณเทคนิคอล SELL (กำไรขณะนี้ +{pnl_pct:.2f}%)"
        elif pnl_pct <= -1.5:
            return True, "TECH_SELL", f"📉 สัญญาณเทคนิคอล SELL + ข่าวไม่สนับสนุน -> ขายตัดความเสี่ยง ({pnl_pct:.2f}%)"

    return False, "HOLD", "ถือครองตามแผนปกติ"
