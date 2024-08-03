import logging
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader

logger = logging.getLogger(__name__)

class NewsAPI:
    def __init__(self, api_key, llm_api_key):
        self.api_key = api_key
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

    def get_news(self, query, num_articles=2):
        logger.info(f'Fetching news for query: {query}')
        params = {
            'q': query,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': num_articles
        }
        response = requests.get('https://newsapi.org/v2/everything', params=params)
        articles = response.json().get('articles', [])
        logger.info(f'Fetched {len(articles)} articles')
        return articles

    def load_articles(self, articles):
        logger.info('Loading articles')
        docs = []
        for article in articles:
            url = article['url']
            loader = WebBaseLoader(url)
            docs.append(loader.load()[0])
            logger.info(f'Loaded article from URL: {url}')
        return docs

    async def send_news(self, update, context):
        query = ' '.join(context.args)
        logger.info(f'User requested news with query: {query}')
        articles = self.get_news(query)
        
        if not articles:
            logger.info('No news articles found')
            await update.message.reply_text('No news found.')
            return

        docs = self.load_articles(articles)
        
        summaries = []
        for doc, article in zip(docs, articles):
            url = article['url']
            context_text = doc.page_content
            question = "요약해줘"
            try:
                result = self.chain_with_context.invoke({"context": context_text, "question": question})
                summaries.append((url, result))
                logger.info('Generated summary for an article')
            except Exception as e:
                logger.error(f'Error generating summary: {e}')
        
        context.user_data['articles'] = summaries
        context.user_data['full_articles'] = docs

        for url, summary in summaries:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=url)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"요약:\n\n{summary}")
            logger.info('Sent URL and summary to user')
