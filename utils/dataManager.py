class DataManager:
    def __init__(self, context):
        self.context = context
        self.keys = ['articles', 'full_articles', 'reddit_posts', 'full_reddit_posts','realestate']

    def initialize(self, keys=None):
        if keys is None:
            keys = self.keys
        for key in keys:
            self.context.user_data[key] = []

    def add_data(self, key, value):
        if key in self.context.user_data:
            self.context.user_data[key].append(value)
        else:
            self.context.user_data[key] = [value]

    def get_data(self, key):
        return self.context.user_data.get(key, [])
