import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import yfinance as yf
import numpy as np
import pandas as pd

# =========================
# PAGE
# =========================
st.set_page_config(page_title="Stable Quant App", page_icon="📊")
st.title("📊 穩定版量化交易系統")

# =========================
# ONLY SHEETS SCOPE（穩定關鍵）
# =========================
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)

# ⚠️ 用 ID（穩定，不用 Drive）
SHEET_ID = "你的SpreadsheetID"
sheet = client.open_by_key(SHEET_ID).sheet1

# =========================
# SAFE DATA
# =========================
def get_price(symbol):
    df = yf.download(symbol, period="6mo", auto_adjust=True, progress=False)
    return float(df["Close"].to_numpy()[-1])

# =========================
# GOOGLE SHEETS
# =========================
def save_trade(stock, side, qty, price):
    sheet.append_row([stock, side, qty, price])

def load_trades():
    return pd.DataFrame(sheet.get_all_records())

# =========================
# UI
# =========================
stocks = {
    "台積電": "2330.TW",
    "鴻海": "2317.TW",
    "輝達": "NVDA",
    "特斯拉": "TSLA"
}

name = st.selectbox("股票", list(stocks.keys()))
symbol = stocks[name]

qty = st.number_input("數量", 1, 1000, 1)

price = get_price(symbol)

st.write("現價：", price)

# =========================
# TRADE
# =========================
col1, col2 = st.columns(2)

with col1:
    if st.button("BUY"):
        save_trade(name, "BUY", qty, price)
        st.success("BUY 已存到 Google Sheets")

with col2:
    if st.button("SELL"):
        save_trade(name, "SELL", qty, price)
        st.success("SELL 已存到 Google Sheets")

# =========================
# HISTORY
# =========================
st.subheader("📜 交易紀錄")
st.dataframe(load_trades())
