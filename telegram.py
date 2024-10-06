import requests


class TelegramBot:

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def send_md(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        response = requests.post(url,
                                 {
                                     'chat_id': self.chat_id
                                     , 'parse_mode': 'Markdown'
                                     , 'text': message
                                 })
        if response.status_code != 200:
            raise Exception(f"Couldn't send telegram message: {response.content}")

    def send_code(self, message):
        self.send_md(f'```\n{message}\n```')