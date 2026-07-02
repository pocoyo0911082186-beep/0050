import yfinance as yf
import traceback
import streamlit as st
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =========================
# PAGE
# =========================
st.set_page_config(page_title="Stable Trading App", page_icon="📊")
st.title("📊 Stable Quant Trading System")

# =========================
# GOOGLE SHEETS (NO DRIVE)
# =========================
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

SHEET_ID = "1BOK77GxxCDVesPJVLkf_hR36gksv8U3Bsptb0yvdyKo"
sheet = client.open_by_key(SHEET_ID).sheet1

# =========================
# SAFE PRICE FUNCTION
# =========================
def get_price(symbol):
    try:
        df = yf.download(
            symbol,
            period="6mo",
            auto_adjust=True,
            progress=False
        )

        print(df)
        print(df.columns)
        print(df.head())
        if df.empty:
            print("DataFrame 是空的")
            return None

        print(df.columns)

        close = df["Close"].dropna()

        print(close)

        return float(close.iloc[-1])

    except Exception as e:
        print(e)
        traceback.print_exc()
        return None

# =========================
# SHEETS FUNCTIONS
# =========================
def save_trade(stock, side, qty, price):
    try:
        sheet.append_row([stock, side, qty, price])
    except:
        st.error("寫入失敗（請檢查 Google Sheet 權限）")

def load_trades():
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except:
        return pd.DataFrame()

# =========================
# UI
# =========================
stocks = {
    "台積電": "2330.TW",
    "鴻海": "2317.TW",
    "輝達": "NVDA",
    "特斯拉": "TSLA"
}

name = st.selectbox("選擇股票", list(stocks.keys()))
symbol = stocks[name]

qty = st.number_input("數量", 1, 1000, 1)

# =========================
# PRICE
# =========================
price = get_price(symbol)

if price is None:
    st.error("❌ 無法取得價格（Yahoo API 暫時無資料）")
    st.stop()

st.metric("現價", price)

# =========================
# TRADE
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("BUY"):
        save_trade(name, "BUY", qty, price)
        st.success("BUY 已記錄")

with col2:
    if st.button("SELL"):
        save_trade(name, "SELL", qty, price)
        st.success("SELL 已記錄")

# =========================
# HISTORY
# =========================
st.subheader("📜 交易紀錄")
df = load_trades()
st.dataframe(df)
