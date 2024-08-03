import logging
import praw
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class RedditAPI:
    def __init__(self, client_id, client_secret, user_agent, llm_api_key):
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
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

    def get_reddit_posts(self, subreddit, limit=2):
        subreddit = self.reddit.subreddit(subreddit)
        hot_posts = subreddit.hot(limit=limit)
        posts = []
        for post in hot_posts:
            if not post.stickied:
                posts.append({
                    'title': post.title,
                    'url': post.url,
                    'score': post.score
                })
        return posts

    async def send_reddit_posts(self, update, context):
        subreddit = ' '.join(context.args) if context.args else 'news'
        posts = self.get_reddit_posts(subreddit)
        
        if not posts:
            await update.message.reply_text('No posts found.')
            return

        summaries = []
        for post in posts:
            title = post['title']
            url = post['url']
            score = post['score']
            post_text = f"{title}\n\n{url}\n\nScore: {score}"
            question = "요약해줘"
            try:
                result = self.chain_with_context.invoke({"context": post_text, "question": question})
                summaries.append((url, result))
                logger.info('Generated summary for a reddit post')
            except Exception as e:
                logger.error(f'Error generating summary: {e}')

        for url, summary in summaries:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=url)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"요약:\n\n{summary}")
            logger.info('Sent URL and summary to user')
