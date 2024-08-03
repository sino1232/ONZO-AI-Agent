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

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# NewsAPI 설정
NEWS_API_KEY = 'ea8d3aab557e49b7b8627eae2892a8eb'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# 텔레그램 봇 설정
TELEGRAM_BOT_TOKEN = '6109044335:AAFMaGQ8QKeRWlxnVasivhjv1MYg-9nkXMg'

# Reddit API 설정
REDDIT_CLIENT_ID = 'c4HHOzrXyR0SeEBAFLmZoQ'
REDDIT_CLIENT_SECRET = 'JkwXpy7tyJSMiog4kf9oI5fNG6wu6Q'
REDDIT_USER_AGENT = 'myRedditApp/0.1'

# Reddit API 클라이언트 설정
reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    user_agent=REDDIT_USER_AGENT
)

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
        
        if any(keyword in result for keyword in ["없습니다", "모릅니다", "알 수 없습니다", "정보가 없습니다", "There is no", "context", "이 문서"]) or result.strip() == "" or len(result) < 20:
            # 문서에서 정보를 찾지 못했을 경우, 일반적인 체인을 사용하여 응답합니다.
            logger.info('No relevant information found in the context, using general model')
            result = chain_without_context.invoke({"question": user_question})
        
        await update.message.reply_text(result)
        logger.info('Sent answer to user question')
    else:
        result = chain_without_context.invoke({"question": user_question})
        await update.message.reply_text(result)
        logger.info('Sent general answer to user question without context')

def get_reddit_posts(subreddit, limit=5):
    subreddit = reddit.subreddit(subreddit)
    hot_posts = subreddit.hot(limit=limit)
    posts = []
    for post in hot_posts:
        if not post.stickied:  # 상단 고정된 게시물 제외
            posts.append({
                'title': post.title,
                'url': post.url,
                'score': post.score,
                'selftext': post.selftext  # 게시물 내용 추가
            })
    return posts

async def send_reddit_posts(update: Update, context: CallbackContext):
    subreddit = ' '.join(context.args) if context.args else 'news'
    posts = get_reddit_posts(subreddit)
    
    if not posts:
        await update.message.reply_text('No posts found.')
        return

    summaries = []
    for post in posts:
        title = post['title']
        url = post['url']
        score = post['score']
        content = post['selftext']
        
        # Reddit 게시물의 내용을 콘솔에 출력하여 충분한 내용이 있는지 확인
        logger.info(f"Reddit post content: {content}")
        
        question = "요약해줘"
        try:
            # 게시물 내용이 짧을 경우 제목과 URL을 포함하여 요약 요청
            if len(content) < 100:
                content = f"Title: {title}\nURL: {url}\n\n{content}"
            
            result = chain_with_context.invoke({"context": content, "question": question})
            summaries.append((title, url, score, result))
            logger.info('Generated summary for a Reddit post')
        except Exception as e:
            logger.error(f'Error generating summary for Reddit post: {e}')
            summaries.append((title, url, score, "요약 중 오류가 발생했습니다."))

    for title, url, score, summary in summaries:
        message = f"{title}\nScore: {score}\n{url}\n\n요약:\n{summary}"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def main():
    logger.info('Starting bot')
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("news", send_news))
    application.add_handler(CommandHandler("reddit", send_reddit_posts))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    application.run_polling()
    logger.info('Bot is polling for updates')

if __name__ == '__main__':
    main()
