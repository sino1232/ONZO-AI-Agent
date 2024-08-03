import logging
import os
import sys

# api 폴더의 경로를 sys.path에 추가합니다.
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 각 모듈에서 필요한 클래스 가져오기
from news import NewsAPI
from reddit import RedditAPI

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def load_config(file_path):
    config = {}
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:  # 빈 줄, 주석, '='가 없는 줄 무시
                key, value = line.split('=', 1)
                config[key] = value
    return config

config = load_config('config/apikey.txt')

TELEGRAM_BOT_TOKEN = config['TELEGRAM_BOT_TOKEN']

news_api = NewsAPI(api_key=config['NEWS_API_KEY'], llm_api_key=config['LLM_API_KEY'])
reddit_api = RedditAPI(client_id=config['REDDIT_CLIENT_ID'], client_secret=config['REDDIT_CLIENT_SECRET'], user_agent=config['REDDIT_USER_AGENT'], llm_api_key=config['LLM_API_KEY'])
#stock_api = StockAPI(api_url=config['STOCK_API_URL'], llm_api_key=config['LLM_API_KEY'])

# handle_question 함수 추가
async def handle_question(update, context):
    user_question = update.message.text
    logger.info(f'User asked a question: {user_question}')
    
    if 'articles' in context.user_data and context.user_data['articles']:
        context_texts = "\n\n".join(summary for _, summary in context.user_data['articles'])
        result = news_api.chain_with_context.invoke({"context": context_texts, "question": user_question})
        
        if any(keyword in result for keyword in ["없습니다", "모릅니다", "알 수 없습니다", "정보가 없습니다","There is no","context","이 문서"]) or result.strip() == "" or len(result) < 20:
            logger.info('No relevant information found in the context, using general model')
            result = news_api.llm.invoke({"question": user_question})
        
        await update.message.reply_text(result)
        logger.info('Sent answer to user question')
    else:
        result = news_api.llm.invoke({"question": user_question})
        await update.message.reply_text(result)
        logger.info('Sent general answer to user question without context')

def main():
    logger.info('Starting bot')
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("news", news_api.send_news))
    application.add_handler(CommandHandler("reddit", reddit_api.send_reddit_posts))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))

    application.run_polling(poll_interval=60)

    logger.info('Bot is polling for updates')

if __name__ == '__main__':
    main()
