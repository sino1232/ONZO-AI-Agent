import logging
import os
import sys
import time

# api 폴더의 경로를 sys.path에 추가합니다.
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 각 모듈에서 필요한 클래스 가져오기 from 파일명 import Class
from news import NewsAPI
from reddit import RedditAPI
from realestate import RealEstateAPI
from stock import StockAPI

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

config = load_config('config/apikey2.txt')

TELEGRAM_BOT_TOKEN = config['TELEGRAM_BOT_TOKEN']

news_api = NewsAPI(api_key=config['NEWS_API_KEY'], llm_api_key=config['LLM_API_KEY'])
reddit_api = RedditAPI(client_id=config['REDDIT_CLIENT_ID'], client_secret=config['REDDIT_CLIENT_SECRET'], user_agent=config['REDDIT_USER_AGENT'], llm_api_key=config['LLM_API_KEY'])
realestate_api = RealEstateAPI(api_key=config['REALESTATE_API_KEY'], llm_api_key=config['LLM_API_KEY'])
stock_api = StockAPI(llm_api_key=config['LLM_API_KEY'])
#stock_api = StockAPI(api_url=config['STOCK_API_URL'], llm_api_key=config['LLM_API_KEY'])

async def handle_question(update, context):
    user_question = update.message.text
    logger.info(f'User asked a question: {user_question}')
    
    prompt = f"질문에 대한 답변을 한국어로 200자까지만 답해주세요. 근데 더 답을 해야 합리적인 경우엔 더 답변을 해줘도 돼요.\n\n질문: {user_question}"
    
    start_time = time.time()  # Start time for measuring

    # 컨텍스트 데이터 초기화
    context_texts = ""

    #News API 
    if 'articles' in context.user_data and context.user_data['articles']:
        context_texts = "\n\n".join(summary for _, summary in context.user_data['articles'])
    if 'full_articles' in context.user_data and context.user_data['full_articles']:
        context_texts += "\n\n".join(context.user_data['full_articles'])
    
    #Reddit API
    if 'reddit_posts' in context.user_data and context.user_data['reddit_posts']:
        context_texts += "\n\n".join(summary for summary in context.user_data['reddit_posts'])
    if 'full_reddit_posts' in context.user_data and context.user_data['full_reddit_posts']:
        context_texts += "\n\n".join(context.user_data['full_reddit_posts'])
    
    #부동산 API
    if 'realestate' in context.user_data and context.user_data['realestate']:
        context_texts += "\n\n".join(context.user_data['realestate'])
           
     # 주식 API
    if 'stock_prices' in context.user_data and context.user_data['stock_prices']:
        context_texts += "\n\n".join(f"{ticker}: {price}" for ticker, price in context.user_data['stock_prices'].items())
    if 'full_stock_data' in context.user_data and context.user_data['full_stock_data']:
        stock_data = context.user_data['full_stock_data']
        context_texts += "\n".join(f"{key}: {value}" for key, value in stock_data.items())
                   
    logger.info(f'context_texts: {context_texts}')
    
    if context_texts:
        input_text = f"Context: {context_texts}\n\n{prompt}"
        llm_start_time = time.time()  # LLM API 호출 시작 시간
        result = news_api.llm.invoke(input_text)
        llm_end_time = time.time()  # LLM API 호출 종료 시간
        
        logger.info(f'LLM API call time with context: {llm_end_time - llm_start_time:.2f} seconds')
        
        result_content = result.content if hasattr(result, 'content') else str(result)
        if any(keyword in result_content for keyword in ["없습니다", "모릅니다", "알 수 없습니다", "정보가 없습니다", "There is no", "context", "이 문서"]) or result_content.strip() == "" or len(result_content) < 20:
            logger.info('No relevant information found in the context, using general model')
            llm_start_time = time.time()  # 일반 모델 LLM API 호출 시작 시간
            result = news_api.llm.invoke(prompt)
            llm_end_time = time.time()  # 일반 모델 LLM API 호출 종료 시간
            
            logger.info(f'LLM API call time without context: {llm_end_time - llm_start_time:.2f} seconds')
        
        result_text = result.content if hasattr(result, 'content') else str(result)
        await update.message.reply_text(result_text)
        logger.info('Sent answer to user question')
    else:
        llm_start_time = time.time()  # 일반 모델 LLM API 호출 시작 시간
        result = news_api.llm.invoke(prompt)
        llm_end_time = time.time()  # 일반 모델 LLM API 호출 종료 시간
        
        logger.info(f'LLM API call time without context: {llm_end_time - llm_start_time:.2f} seconds')
        
        result_text = result.content if hasattr(result, 'content') else str(result)
        await update.message.reply_text(result_text)
        logger.info('Sent general answer to user question without context')
    
    end_time = time.time()  # End time for measuring
    logger.info(f'Total time taken to handle question: {end_time - start_time:.2f} seconds')

def main():
    logger.info('Starting bot')
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("news", news_api.send_news))
    application.add_handler(CommandHandler("reddit", reddit_api.send_reddit_posts))
    application.add_handler(CommandHandler("realestate", realestate_api.send_real_estate_summaries))
    application.add_handler(CommandHandler("stock", stock_api.send_stock_data))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question))
    
    
 
    #서버에 부담을 주고싶지 않다면 poll_interval을 아래와 같이 60초 늘리세요.
    # application.run_polling(poll_interval=60)
    
    #아래 명령어는 요청이 오는 즉시 응답을 주는 것입니다.
    application.run_polling()

    logger.info('Bot is polling for updates')

if __name__ == '__main__':
    main()
