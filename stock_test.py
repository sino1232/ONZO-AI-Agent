import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import telegram
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser
import praw


llm = ChatGroq(
    temperature=0,
    model="llama3-8b-8192",
    api_key="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",
)

system_context = "Answer the question from given contexts. Answer in Korean."
human_with_context = """
Context: {context}

---

Question: {question}
"""

system_general = "Answer the following question. Answer in Korean."
human_without_context = """
Question: {question}
"""

prompt_with_context = ChatPromptTemplate.from_messages([("system", system_context), ("human", human_with_context)])
prompt_without_context = ChatPromptTemplate.from_messages([("system", system_general), ("human", human_without_context)])

chain_with_context = prompt_with_context | llm | StrOutputParser()
chain_without_context = prompt_without_context | llm | StrOutputParser()



def get_stock_data(symbol, period='5y', interval='1d'):
    stock = yf.Ticker(symbol)
    data = stock.history(period=period, interval=interval)
    return data

def calculate_technical_indicators(data):
    data['SMA20'] = data['Close'].rolling(window=20).mean()
    data['SMA50'] = data['Close'].rolling(window=50).mean()
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['UpperBand'] = data['Close'].rolling(window=20).mean() + (data['Close'].rolling(window=20).std() * 2)
    data['LowerBand'] = data['Close'].rolling(window=20).mean() - (data['Close'].rolling(window=20).std() * 2)
    return data

def get_fundamental_data(symbol):
    stock = yf.Ticker(symbol)
    info = stock.info
    financials = stock.financials
    balance_sheet = stock.balance_sheet
    cashflow = stock.cashflow
    
    five_years_revenue = stock.financials.loc['Total Revenue'].head(5).tolist()
    five_years_operating_income = stock.financials.loc['Operating Income'].head(5).tolist()
    five_years_operating_margin = [(op_inc / rev) * 100 if rev != 0 else 0 for op_inc, rev in zip(five_years_operating_income, five_years_revenue)]
    
    return {
        "Name": info.get('longName', 'N/A'),
        "Sector": info.get('sector', 'N/A'),
        "Industry": info.get('industry', 'N/A'),
        "Market Cap": info.get('marketCap', 'N/A'),
        "주가수익비율 (PER)": info.get('forwardPE', 'N/A'),
        "주가순자산비율 (PBR)": info.get('priceToBook', 'N/A'),
        "주당순이익 (EPS)": info.get('trailingEps', 'N/A'),
        "배당수익률": info.get('dividendYield', 'N/A'),
        "부채비율": info.get('debtToEquity', 'N/A'),
        "5년 매출액 추세": five_years_revenue,
        "5년 영업이익 추세": five_years_operating_income,
        "5년 매출액 대비 영업이익 비율 추세": five_years_operating_margin
    }

def plot_indicators(data, symbol, fundamental_data):
    plt.figure(figsize=(14, 12))

    plt.subplot(3, 1, 1)
    plt.plot(data.index, data['Close'], label='Close Price')
    plt.plot(data.index, data['SMA20'], label='20-Day SMA', color='orange')
    plt.plot(data.index, data['SMA50'], label='50-Day SMA', color='purple')
    plt.fill_between(data.index, data['UpperBand'], data['LowerBand'], color='grey', alpha=0.3)
    plt.title(f"{symbol} Stock Price and Indicators")
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(data.index, data['RSI'], label='RSI', color='blue')
    plt.axhline(70, color='red', linestyle='--')
    plt.axhline(30, color='green', linestyle='--')
    plt.title('Relative Strength Index')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(data.index, data['Volume'], label='Volume', color='black')
    plt.title('Volume')
    plt.legend()

    plt.tight_layout()
    file_path = f"{symbol}_analysis.png"
    plt.savefig(file_path)
    plt.close()

    plt.figure(figsize=(14, 8))
    years = range(len(fundamental_data["5년 매출액 추세"]))
    plt.subplot(3, 1, 1)
    plt.plot(years, fundamental_data["5년 매출액 추세"], marker='o', label='Revenue')
    plt.title('5-Year Revenue Trend')
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(years, fundamental_data["5년 영업이익 추세"], marker='o', label='Operating Income', color='orange')
    plt.title('5-Year Operating Income Trend')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(years, fundamental_data["5년 매출액 대비 영업이익 비율 추세"], marker='o', label='Operating Margin', color='green')
    plt.title('5-Year Operating Margin Trend')
    plt.legend()

    plt.tight_layout()
    file_path_trends = f"{symbol}_trends.png"
    plt.savefig(file_path_trends)
    plt.close()

    return file_path, file_path_trends

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = '6109044335:AAFMaGQ8QKeRWlxnVasivhjv1MYg-9nkXMg'

async def stock_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        symbol = context.args[0].upper()
        data = get_stock_data(symbol)
        if not data.empty:
            data = calculate_technical_indicators(data)
            fundamental_data = get_fundamental_data(symbol)
            file_path, file_path_trends = plot_indicators(data, symbol, fundamental_data)

            fundamental_info = f"{symbol} Fundamental Data:\n"
            for key, value in fundamental_data.items():
                fundamental_info += f"{key}: {value}\n"

            await update.message.reply_photo(photo=open(file_path, 'rb'))
            await update.message.reply_photo(photo=open(file_path_trends, 'rb'))
            await update.message.reply_text(fundamental_info)
        else:
            await update.message.reply_text("No data found for the provided symbol.")
    else:
        await update.message.reply_text("Please provide a stock symbol.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("analyze", stock_analysis))

    application.run_polling()

if __name__ == '__main__':
    main()
