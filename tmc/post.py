import re

from bs4 import BeautifulSoup, Tag
import datetime
import requests


class Post:
    def __init__(self, post: Tag = None, thread_title: str = None, db_entry=None):
        if post:
            self.build_from_post(post, thread_title)
        else:
            self.build_from_db(db_entry)

    def build_from_post(self, post, thread_title):
        try:
            self.id = int(
                re.search('\/posts\/(\d+)\/', str(post)).group(1)
            )
        except AttributeError:
            raise AttributeError
        print("Post ID is ", self.id)
        self.thread_title = thread_title.replace("'", "\\'").replace('"', '\\"').split('Discussion in ')[0].strip()
        self.username = post.find('a', class_='username').text
        self.posted_at = post.find('time').get('datetime')

        self.reply_ids = []

        post, self.reply_ids = self.clean_message(post)
        self.message = post.find('div', class_='bbWrapper').text.replace('â†‘', '\n"').replace(
            'Click to expand...', '\n"').strip()
        self.media = self.get_media(post)

        output_list = post.find('ul', class_='dark_postrating_outputlist')
        output_dict = self.parse_output_list(output_list)

        self.likes = output_dict.get('Like', 0)
        self.loves = output_dict.get('Love', 0)
        self.helpful = output_dict.get('Helpful', 0)

        self.sentiment = 0

    def build_from_db(self, db_entry):
        if type(db_entry) == dict:
            self.id = db_entry['id']
            self.username = db_entry['username']
            self.posted_at = db_entry['posted_at']
            self.message = db_entry['message']
            self.media = db_entry['media']
            self.likes = db_entry['likes']
            self.loves = db_entry['loves']
            self.helpful = db_entry['helpful']
            self.sentiment = db_entry['sentiment']
        else:
            raise TypeError(f'Building from type {type(db_entry)} not supported yet.')

    @staticmethod
    def parse_output_list(output_list: dict):
        """
        Helper function for cleanly accessing like/love/helpful counts.
        """

        output_dict = {}

        try:
            outputs = [i.text.strip() for i in output_list.find_all('li')]
        except AttributeError:
            return output_dict

        for output in outputs:
            attr, value = output.split(' x ')
            value = int(value)
            output_dict[attr] = value

        return output_dict

    @staticmethod
    def get_media(post: Tag):
        """
        Retrieves media's URL, if any.
        """

        iframe = post.find('iframe')

        if iframe:
            return iframe.get('src')

    def clean_message(self, post):
        quotes = post.find_all('blockquote')
        replies = []
        for quote in quotes:
            replies.append(quote.extract())

        reply_ids = []

        for reply in replies:
            try:
                reply_ids.append(reply.find('a', class_='bbCodeBlock-sourceJump').get('href').split('=')[-1])
            except AttributeError:
                continue

        return post, reply_ids

    def get_sentiment(self, session=requests.Session(), google_api_key=None):
        """
        Gets sentiment data of post.
        """
        if not google_api_key:
            raise (ValueError('Calling this method requires a valid google_api_key for the Cloud Natural Voice API.'))
        r = session.post(
            f'https://language.googleapis.com/v1/documents:analyzeSentiment?fields=documentSentiment%2Clanguage&key={google_api_key}',
            json={"document": {"content": self.message,
                               "type": "PLAIN_TEXT"}
                  }
            )
        self.sentiment = r.json()

        return

    def upload_to_db(self, db_connection):
        message = self.message.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        username = self.username.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        sql_statement = "INSERT INTO `posts` (`id`, `thread_title`, `username`, `posted_at`, `message`, `likes`, "
        sql_statement += f"`loves`, `helpful`, `sentiment`, `in_reply_to`) VALUES ('{self.id}', '{self.thread_title}', "
        sql_statement += f"'{username}', '{self.posted_at}', '{message}',"
        sql_statement += f" {self.likes}, {self.loves}, {self.helpful}, {self.sentiment}, '{','.join(self.reply_ids)}')"
        print(sql_statement)
        with db_connection.cursor() as cursor:
            cursor.execute(sql_statement)
            db_connection.commit()
        return


class Thread(Post):
    """
    Effectively a Post with a title.
    """

    def __init__(self, title: str, post: Tag):
        super(Thread, self).__init__()
        self.title = title
