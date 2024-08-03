import logging
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class StockAPI:
    def __init__(self, api_url, llm_api_key):
        self.api_url = api_url
        self.llm = ChatGroq(
            temperature=0,
            model="llama3-8b-8192",
            api_key=llm_api_key,
        )
        self.system_context = "Answer the question from given contexts. Answer in Korean."
        self.human_with_context = """
        Context: {context}

        ---

        Question: {question}
        """
        self.prompt_with_context = ChatPromptTemplate.from_messages([("system", self.system_context), ("human", self.human_with_context)])
        self.chain_with_context = self.prompt_with_context | self.llm | StrOutputParser()

    async def analyze_stock(self, update, context):
        stock_symbol = ' '.join(context.args).upper()
        logger.info(f'User requested stock analysis for: {stock_symbol}')
        
        stock_api_url = f'{self.api_url}{stock_symbol}'
        response = requests.get(stock_api_url)
        
        if response.status_code != 200:
            logger.error(f'Error fetching stock data: {response.status_code}')
            await update.message.reply_text('주식 정보를 가져오는데 실패했습니다.')
            return
        
        stock_data = response.json()
        context_text = f"현재 주가: {stock_data['price']}\n변동률: {stock_data['change_percent']}\n시가총액: {stock_data['market_cap']}"
        question = "주식 정보를 요약해줘"
        
        try:
            result = self.chain_with_context.invoke({"context": context_text, "question": question})
            await update.message.reply_text(result)
            logger.info('Sent stock analysis to user')
        except Exception as e:
            logger.error(f'Error generating stock analysis: {e}')
            await update.message.reply_text('주식 정보를 요약하는데 실패했습니다.')
