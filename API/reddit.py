import praw
from apibase import APIBase  # APIBase 클래스를 import
from utils.dataManager import DataManager  # APIBase 클래스를 import

class RedditAPI(APIBase):
    def __init__(self, client_id, client_secret, user_agent, llm_api_key):
        super().__init__(llm_api_key)
        try:
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )
            self.reddit.user.me()  # 인증 테스트
        except Exception as e:
            self.logger.error(f"Failed to authenticate Reddit API: {e}")
            raise

    def get_reddit_posts(self, subreddit=None, limit=1):
        posts = []
        try:
            if subreddit:
                subreddit = self.reddit.subreddit(subreddit)
                hot_posts = subreddit.hot(limit=limit)
            else:
                hot_posts = self.reddit.front.hot(limit=limit)
                
            for post in hot_posts:
                if not post.stickied:
                    try:
                        # Post details
                        score = post.score
                        post_text = post.selftext  # Post content
                        
                        # Fetch comments
                        post.comments.replace_more(limit=0)  # Avoid "MoreComments" objects
                        comments = [f"{index+1}. {comment.body}" for index, comment in enumerate(post.comments.list())]
                        
                        posts.append({
                            'title': post.title,
                            'url': post.url,
                            'score': score,
                            'content': post_text,
                            'comments': comments
                        })
                    except AttributeError as e:
                        self.logger.error(f"AttributeError: {e} - post: {post.title}")
            posts.sort(key=lambda x: x['score'], reverse=True)
        except Exception as e:
            self.logger.error(f"Error accessing subreddit: {e}")
            if subreddit:
                return self.get_reddit_posts(limit=limit)
        return posts[:limit]
        
    async def send_reddit_posts(self, update, context):
        data_manager = DataManager(context)
        data_manager.initialize(['articles', 'full_articles', 'reddit_posts', 'full_reddit_posts', 'realestate','stock_prices', 'full_stock_data'])  # 필요한 데이터만 초기화
        
        # 초기화 후 user_data의 상태를 로그로 확인
        self.logger.info(f'User data after initialization: {context.user_data}')

        subreddit = ' '.join(context.args) if context.args else None
        posts = self.get_reddit_posts(subreddit)
        
        if not posts and subreddit:
            await update.message.reply_text(f'Not found subreddit "{subreddit}". So I will get a post you may like.')
            posts = self.get_reddit_posts(None)
        
        if not posts:
            await update.message.reply_text('No posts found.')
            return

        post = posts[0]  # Only use the first post
        title = post['title']
        url = post['url']
        score = post['score']
        content = post['content']
        comments = post['comments']
        
        # Combine post content and comments into a single text
        contents = f"{title}\n\nContents:{content}\n\nURL:{url}\n\nScore:{score}"
        combined_text = f"{title}\n\nContents:{content}\n\nComments:\n" + "\n".join(comments)
        
        question = "한국어로 요약해줘"
        try:
            summary_result = self.chain_with_context.invoke({"context": contents, "question": question})
            
            # summary_result가 무엇을 반환하는지 확인하기 위해 로그로 출력
            self.logger.info(f'summary_result: {summary_result}')
            
            # 요약을 파싱하는 대신, 전체 요약을 사용
            summary = summary_result.strip()

            self.logger.info('Generated summary for a reddit post')
        except Exception as e:
            self.logger.error(f'Error generating summary: {e}')
            return

        context.user_data['reddit_posts'] = [summary]
        context.user_data['full_reddit_posts'] = [combined_text]
        self.logger.info(f'full_reddit_posts {context.user_data["full_reddit_posts"]}')
        
        await context.bot.send_message(chat_id=update.effective_chat.id, text=url)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"요약:\n\n{summary}\n\npost:\n\n{content}")
        self.logger.info('Sent URL and summary to user')
