import logging
import requests
from langchain_community.document_loaders import WebBaseLoader
from apibase import APIBase  # APIBase 클래스를 import
from utils.dataManager import DataManager  # DataManager 클래스를 import

logger = logging.getLogger(__name__)

class NewsAPI(APIBase):
    def __init__(self, api_key, llm_api_key):
        super().__init__(llm_api_key)
        self.api_key = api_key

    def get_news(self, query, num_articles=1):
        self.logger.info(f'Fetching news for query: {query}')
        params = {
            'q': query,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': num_articles
        }
        response = requests.get('https://newsapi.org/v2/everything', params=params)
        articles = response.json().get('articles', [])
        self.logger.info(f'Fetched {len(articles)} articles')
        return articles

    def load_articles(self, articles):
        self.logger.info('Loading articles')
        docs = []
        for article in articles:
            url = article['url']
            loader = WebBaseLoader(url)
            docs.append(loader.load()[0])
            self.logger.info(f'Loaded article from URL: {url}')
        return docs

    async def send_news(self, update, context):
        data_manager = DataManager(context)
        data_manager.initialize(['articles', 'full_articles','reddit_posts','full_reddit_posts','realestate','stock_prices', 'full_stock_data'])  # 필요한 데이터만 초기화
     
        # 초기화 후 user_data의 상태를 로그로 확인
        self.logger.info(f'User data after initialization: {context.user_data}')

        query = ' '.join(context.args)
        self.logger.info(f'User requested news with query: {query}')
        articles = self.get_news(query)
        
        if not articles:
            self.logger.info('No news articles found')
            await update.message.reply_text('No news found.')
            return

        docs = self.load_articles(articles)
        
        summaries = []
        full_articles = []
        for doc, article in zip(docs, articles):
            url = article['url']
            context_text = doc.page_content

            # 텍스트 클리닝: 불필요한 공백, 특수 문자 제거
            cleaned_context_text = context_text.replace('\n', ' ').replace('\xa0', ' ').strip()

            # 텍스트 길이 제한: 너무 긴 경우 자르기
            if len(cleaned_context_text) > 1000:  # 임의로 1000자로 제한
                cleaned_context_text = cleaned_context_text[:1000] + "..."

            full_articles.append(cleaned_context_text)
            question = "한국어로 요약해줘"

            try:
                # 요약 요청 시 예외 처리 추가
                result = self.chain_with_context.invoke({"context": cleaned_context_text, "question": question})
                summaries.append((url, result))
                self.logger.info('Generated summary for an article')
            except Exception as e:
                self.logger.error(f'Error generating summary: {e}')
            
        context.user_data['articles'] = summaries
        context.user_data['full_articles'] = full_articles
        
        self.logger.info(f'Generated summaries: {summaries}')
        
        for url, summary in summaries:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=url)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"요약:\n\n{summary}")
            self.logger.info('Sent URL and summary to user')

