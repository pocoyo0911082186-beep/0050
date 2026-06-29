import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt
import gspread
from google.oauth2.service_account import Credentials
from sklearn.linear_model import LinearRegression

# =========================
# Page
# =========================
st.set_page_config(page_title="V6 Quant System", page_icon="📊")
st.title("📊 V6 雲端量化交易系統（GitHub版）")

# =========================
# Google Sheets（雲端）
# =========================
SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPE
)

client = gspread.authorize(creds)
sheet = client.open("TradingLog").sheet1

def save_trade(stock, side, qty, price):
    sheet.append_row([stock, side, qty, price])

def load_trades():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# =========================
# Data safe load
# =========================
def safe_download(symbol, period="1y"):
    df = yf.download(symbol, period=period, auto_adjust=True)

    if df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)

    return df

# =========================
# RSI
# =========================
def rsi(df, period=14):
    delta = df["Close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1/period).mean()
    avg_loss = loss.ewm(alpha=1/period).mean()

    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

# =========================
# Strategy MA
# =========================
def strategy(df):
    df["MA5"] = df["Close"].rolling(5).mean()
    df["MA20"] = df["Close"].rolling(20).mean()

    df["signal"] = 0
    df.loc[df["MA5"] > df["MA20"], "signal"] = 1
    df.loc[df["MA5"] < df["MA20"], "signal"] = -1

    return df

# =========================
# Backtest
# =========================
def backtest(df, cash=100000):

    stock = 0
    equity = []

    for i in range(len(df)):

        price = df["Close"].iloc[i]
        signal = df["signal"].iloc[i]

        if signal == 1 and cash > price:
            stock = cash // price
            cash -= stock * price

        elif signal == -1 and stock > 0:
            cash += stock * price
            stock = 0

        equity.append(cash + stock * price)

    df["equity"] = equity
    return df

# =========================
# Metrics
# =========================
def max_drawdown(equity):
    peak = equity[0]
    mdd = 0

    for x in equity:
        peak = max(peak, x)
        mdd = max(mdd, (peak - x) / peak)

    return mdd

def sharpe(equity):
    ret = np.diff(equity) / equity[:-1]
    return np.mean(ret) / (np.std(ret) + 1e-9)

def trend_predict(df):
    x = np.arange(len(df)).reshape(-1, 1)
    y = df["Close"].values.reshape(-1, 1)

    model = LinearRegression()
    model.fit(x, y)

    future = np.arange(len(df), len(df)+5).reshape(-1,1)
    return model.predict(future).flatten()

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

period = st.selectbox("資料區間", ["6mo", "1y", "2y"], index=1)

qty = st.number_input("交易數量", 1, 1000, 1)

df = safe_download(symbol, period)

if df is None:
    st.error("無資料")
    st.stop()

df = df.dropna()
df = rsi(df)
df = strategy(df)
df = backtest(df)

# =========================
# Metrics
# =========================
ret = (df["equity"].iloc[-1] / df["equity"].iloc[0]) - 1
mdd = max_drawdown(df["equity"].values)
sh = sharpe(df["equity"].values)

st.metric("總報酬率", f"{ret*100:.2f}%")
st.metric("最大回撤", f"{mdd*100:.2f}%")
st.metric("Sharpe", f"{sh:.2f}")

# =========================
# Equity Curve
# =========================
st.subheader("📈 Equity Curve")

fig, ax = plt.subplots()
ax.plot(df["equity"])
st.pyplot(fig)

# =========================
# K線 + RSI
# =========================
apds = [
    mpf.make_addplot(df["MA5"], color="blue"),
    mpf.make_addplot(df["MA20"], color="orange"),
    mpf.make_addplot(df["RSI"], panel=1, color="purple"),
    mpf.make_addplot([70]*len(df), panel=1, color="red", linestyle="--"),
    mpf.make_addplot([30]*len(df), panel=1, color="green", linestyle="--"),
]

fig, _ = mpf.plot(
    df,
    type="candle",
    addplot=apds,
    panel_ratios=(3,1),
    style="yahoo",
    returnfig=True
)

st.pyplot(fig)

# =========================
# Trade Buttons
# =========================
st.subheader("💰 模擬交易")

price = float(df["Close"].iloc[-1])

col1, col2 = st.columns(2)

with col1:
    if st.button("BUY"):
        save_trade(name, "BUY", qty, price)
        st.success("BUY 已寫入 Google Sheets")

with col2:
    if st.button("SELL"):
        save_trade(name, "SELL", qty, price)
        st.success("SELL 已寫入 Google Sheets")

# =========================
# Cloud trades
# =========================
st.subheader("📜 雲端交易紀錄")
st.dataframe(load_trades())

# =========================
# Prediction
# =========================
st.subheader("📊 趨勢預測（回歸）")
st.write(trend_predict(df))
