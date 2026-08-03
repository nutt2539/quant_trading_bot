import pandas as pd
from data_loader import fetch_stock_info

def screen_stocks(watchlist: list) -> pd.DataFrame:
    """
    Screen and score stocks based on Fundamental Quality (PE, ROE, Dividend Yield).
    Returns ranked DataFrame of screened candidates.
    """
    results = []
    for symbol in watchlist:
        info = fetch_stock_info(symbol)
        if not info or info.get('price') is None:
            continue
            
        pe = info.get('pe_ratio')
        roe = info.get('roe')
        div_yield = info.get('dividend_yield')
        
        # Calculate Quality Score (0 to 100)
        score = 50 # Base score
        
        # Valuation: Moderate PE (5 to 30) is favorable
        if pe:
            if 0 < pe <= 20:
                score += 20
            elif 20 < pe <= 35:
                score += 10
            elif pe > 40:
                score -= 15

        # Profitability: High ROE (> 15%) is favorable
        if roe:
            roe_pct = roe * 100 if roe < 1 else roe
            if roe_pct >= 20:
                score += 20
            elif roe_pct >= 12:
                score += 10
            elif roe_pct < 5:
                score -= 10

        # Dividend Yield (> 2% adds score)
        if div_yield:
            div_pct = div_yield * 100 if div_yield < 1 else div_yield
            if div_pct >= 3.0:
                score += 10
            elif div_pct >= 1.5:
                score += 5

        score = max(0, min(100, score)) # Clamp between 0 and 100
        
        results.append({
            'Symbol': symbol,
            'Name': info.get('name', symbol),
            'Sector': info.get('sector', 'N/A'),
            'Price': info.get('price'),
            'P/E': round(pe, 2) if pe else 'N/A',
            'ROE (%)': round(roe * 100, 2) if roe else 'N/A',
            'Div Yield (%)': round(div_yield * 100, 2) if div_yield else 'N/A',
            'Quality Score': score,
            'Recommendation': 'BUY' if score >= 70 else ('HOLD' if score >= 50 else 'AVOID')
        })

    df_res = pd.DataFrame(results)
    if not df_res.empty:
        df_res = df_res.sort_values(by='Quality Score', ascending=False).reset_index(drop=True)
    return df_res
