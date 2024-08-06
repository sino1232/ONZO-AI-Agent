import logging
import requests
from langchain_community.document_loaders import WebBaseLoader
from apibase import APIBase  # APIBase 클래스를 import

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
        # 뉴스 관련 컨텍스트 초기화
        context.user_data['articles'] = []
        context.user_data['full_articles'] = []
        
        # Reddit 관련 컨텍스트 초기화
        context.user_data['reddit_posts'] = []
        context.user_data['full_reddit_posts'] = []

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
            full_articles.append(context_text)
            question = "요약해줘"
            try:
                result = self.chain_with_context.invoke({"context": context_text, "question": question})
                summaries.append((url, result))
                self.logger.info('Generated summary for an article')
            except Exception as e:
                self.logger.error(f'Error generating summary: {e}')
            
        context.user_data['articles'] = summaries
        context.user_data['full_articles'] = full_articles

        for url, summary in summaries:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=url)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"요약:\n\n{summary}")
            self.logger.info('Sent URL and summary to user')
