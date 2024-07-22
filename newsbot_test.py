import telegram
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.output_parsers import StrOutputParser

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# httpx 라이브러리의 로그 레벨을 WARNING으로 설정
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

# NewsAPI 설정
NEWS_API_KEY = '' #자신의 API키를 넣으세요.
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN = '' #자신의 API를 넣으세요.

llm = ChatGroq(
    temperature=0,
    model="llama3-8b-8192", #본인이 원하는 모델을 넣으세요.
    api_key="", # 자신의 API를 넣으세요.
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

def get_news(query, num_articles=2):
    logger.info(f'Fetching news for query: {query}')
    params = {
        'q': query,
        'apiKey': NEWS_API_KEY,
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': num_articles
    }
    response = requests.get(NEWS_API_URL, params=params)
    articles = response.json().get('articles', [])
    logger.info(f'Fetched {len(articles)} articles')
    return articles

def load_articles(articles):
    logger.info('Loading articles')
    docs = []
    for article in articles:
        url = article['url']
        loader = WebBaseLoader(url)
        docs.append(loader.load()[0])
        logger.info(f'Loaded article from URL: {url}')
    return docs

async def send_news(update: Update, context: CallbackContext):
    query = ' '.join(context.args)
    logger.info(f'User requested news with query: {query}')
    articles = get_news(query)
    
    if not articles:
        logger.info('No news articles found')
        await update.message.reply_text('No news found.')
        return

    docs = load_articles(articles)
    
    summaries = []
    for doc, article in zip(docs, articles):
        url = article['url']
        context_text = doc.page_content
        question = "요약해줘"
        try:
            result = chain_with_context.invoke({"context": context_text, "question": question})
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



async def handle_question(update: Update, context: CallbackContext):
    user_question = update.message.text
    logger.info(f'User asked a question: {user_question}')
    
    if 'articles' in context.user_data and context.user_data['articles']:
        context_texts = "\n\n".join(summary for _, summary in context.user_data['articles'])
        result = chain_with_context.invoke({"context": context_texts, "question": user_question})
        
        if any(keyword in result for keyword in ["없습니다", "모릅니다", "알 수 없습니다", "정보가 없습니다","There is no","context","이 문서"]) or result.strip() == "" or len(result) < 20:
            # 문서에서 정보를 찾지 못했을 경우, 일반적인 체인을 사용하여 응답합니다.
            logger.info('No relevant information found in the context, using general model')
            result = chain_without_context.invoke({"question": user_question})
        
        await update.message.reply_text(result)
        logger.info('Sent answer to user question')
    else:
        result = chain_without_context.invoke({"question": user_question})
        await update.message.reply_text(result)
        logger.info('Sent general answer to user question without context')

def main():
    logger.info('Starting bot')
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("news", send_news))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    application.run_polling(poll_interval=60)  # 60초마다 업데이트 확인

    logger.info('Bot is polling for updates')

if __name__ == '__main__':
    main()
