import yfinance as yf
import logging
from apibase import APIBase
from utils.dataManager import DataManager
from yahooquery import Ticker
import yahooquery as yq
import pandas as pd
import matplotlib.pyplot as plt
import io
import datetime

class StockAPI(APIBase):
    def __init__(self, llm_api_key):
        super().__init__(llm_api_key)
        self.logger = logging.getLogger(__name__)

    def search_ticker(self, company_name):
        search = yq.search(company_name)
        if 'quotes' in search and len(search['quotes']) > 0:
            return search['quotes'][0]['symbol']
        return None

    def get_top_stocks(self, context, top_n=10):
        # 'stock_prices'와 'full_stock_data'가 딕셔너리로 초기화되어 있는지 확인
        if 'stock_prices' not in context.user_data:
            context.user_data['stock_prices'] = {}
        if 'full_stock_data' not in context.user_data:
            context.user_data['full_stock_data'] = {}

        spy = Ticker("SPY")
        data = spy.fund_holding_info
        
        if data is None or 'SPY' not in data or 'holdings' not in data['SPY']:
            self.logger.error(f"Failed to retrieve holdings for SPY ETF. Holdings: {data}")
            return [], []

        holdings = data['SPY']['holdings']
        df = pd.DataFrame(holdings)
        top_holdings = df.head(top_n)
        top_tickers = top_holdings['symbol'].tolist()

        # 각 종목에 대한 상세 데이터를 가져와 context.user_data에 저장
        top_stock_data = []

        for ticker in top_tickers:
            stock_data = self.get_stock_data(ticker)
            if stock_data:
                top_stock_data.append(stock_data)
                context.user_data['stock_prices'][ticker] = stock_data['current_price']
                context.user_data['full_stock_data'][ticker] = stock_data
                self.logger.info(f'context.user_data: {context.user_data}')
        
        return top_stock_data, top_tickers

    def get_stock_data(self, ticker):
        self.logger.info(f'Fetching stock data for ticker: {ticker}')
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(period="1d")
            info = stock.info
            return {
                'date': data.index[-1].strftime('%Y-%m-%d (%A)'), 
                'current_price': data['Close'].iloc[-1],
                'open': data['Open'].iloc[-1],
                'high': data['High'].iloc[-1],
                'low': data['Low'].iloc[-1],
                'volume': data['Volume'].iloc[-1],
                'market_cap': info.get('marketCap', 'N/A'),
                '52_week_high': info.get('fiftyTwoWeekHigh', 'N/A'),
                '52_week_low': info.get('fiftyTwoWeekLow', 'N/A'),
                'pe_ratio': info.get('forwardPE', 'N/A'),
                'dividend_yield': info.get('dividendYield', 'N/A'),
                'company_name': info.get('shortName', ticker)
            }
        except Exception as e:
            self.logger.error(f"Error fetching data for {ticker}: {e}")
            return None


    async def send_stock_data(self, update, context):
        data_manager = DataManager(context)
        data_manager.initialize(['articles', 'full_articles', 'reddit_posts', 'full_reddit_posts', 'realestate'])
    
        self.logger.info(f'User data after initialization: {context.user_data}')
    
        if context.args:
            last_arg = context.args[-1]
            
            if last_arg.lower() == 'graph':  # 사용자가 'graph'를 입력했는지 확인
                input_query = ' '.join(context.args[:-1]).upper()  # 'graph' 인자를 제외하고 합침
                ticker = self.search_ticker(input_query)
                
                if not ticker:
                    await update.message.reply_text(f'No ticker found for company name "{input_query}". Please try again.')
                    return

                await self.send_stock_graph(update, context, ticker)
                return
            else:
                input_query = ' '.join(context.args).upper()  # 회사명을 온전히 사용
                ticker = self.search_ticker(input_query)
                
                if not ticker:
                    await update.message.reply_text(f'No ticker found for company name "{input_query}". Please try again.')
                    return
        else:
            self.logger.info('No company name or ticker provided, showing top 10 stocks by market cap')
            top_stocks, tickers = self.get_top_stocks(context)
            response_text = "\n\n".join(
                f"{stock['company_name']} ({ticker}): ${stock['current_price']:.2f}" 
                for stock, ticker in zip(top_stocks, tickers)
            )
            await update.message.reply_text(f"Top 10 Stocks from SPY(S&P500):\n\n{response_text}")
            return

        self.logger.info(f'User requested stock data for ticker: {ticker}')
        stock_data = self.get_stock_data(ticker)
        
        if not stock_data:
            self.logger.info('No stock data found or error in API response')
            await update.message.reply_text('No stock data found. Please check the ticker symbol.')
            return

        # Preparing response text
        response_text = (
            f"회사명: {stock_data['company_name']}({ticker})\n"
            f"날짜: {stock_data['date']}\n"
            f"현재가: ${float(stock_data['current_price']):.2f}\n"
            f"시작가: ${float(stock_data['open']):.2f}\n"
            f"최고가: ${float(stock_data['high']):.2f}\n"
            f"최저가: ${float(stock_data['low']):.2f}\n"
            f"거래량: {int(stock_data['volume']):,}\n"
            f"시가총액: ${float(stock_data['market_cap'])}\n"
            f"52-Week 최고가: ${float(stock_data['52_week_high']):.2f}\n"
            f"52-Week 최저가: ${float(stock_data['52_week_low']):.2f}\n"
            f"P/E 비율: {stock_data['pe_ratio']}\n"
            f"배당수익률: {stock_data['dividend_yield']}\n"
        )
        
        # 주식 데이터 누적
        context.user_data.setdefault('stock_prices', {}).update({ticker: stock_data['current_price']})
        context.user_data.setdefault('full_stock_data', {}).update({ticker: stock_data})

        self.logger.info(f'context.user_data after saving stock data: {context.user_data}')

        await context.bot.send_message(chat_id=update.effective_chat.id, text=response_text)
        self.logger.info('Sent stock data to user')




    async def send_stock_graph(self, update, context, ticker):
        stock = yf.Ticker(ticker)
        data = stock.history(period="5y")  # 지난 5년간의 데이터 가져오기
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(data.index, data['Close'], label='Close Price')
        ax.set_title(f'{ticker} Stock Price (Last 5 Years)')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price (USD)')
        ax.legend()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=buf)
        buf.close()

