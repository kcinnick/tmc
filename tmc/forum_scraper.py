import requests

class User:
    def __init__(self):
        self.username = None
        self.member_type = None
        self.joined = None
        self.messages = None
        self.location = None

    def get_info(self, post=None, url=None):
        if post:
            user_info = post.find('div', class_='messageUserInfo')
            self.username = user_info.find('a', class_='username').text
            self.member_type = user_info.find('em', class_='userTitle').text
            extra_user_info = {i.text[:-1]: i.find_next('dd').text.strip() for i in post.find_all('dt')}
            self.joined = extra_user_info['Joined']
            self.messages = ([], extra_user_info['Messages'])
            self.location = extra_user_info['Location']

class Post:
    def __init__(self, post):
        self.id = int(post.find('a', class_='datePermalink').get('href').split('/')[1])
        self.username = post.find('div', class_='messageUserInfo').find('a', class_='username').text
        self.posted_at = post.find('span', class_='DateTime').text
        self.message = post.find('div', class_='messageContent').text.replace('â†‘', '\n"').replace('Click to expand...', '\n"').strip()
        self.media = self.get_media(post)

        output_list = post.find('ul', class_='dark_postrating_outputlist')
        if output_list:
            output_list = output_list.find_all('strong')
            self.likes = int(output_list[0].text)
            self.loves = int(output_list[1].text)
        else:
            self.likes = 0
            self.loves = 0

    def get_media(self, post):
        iframe = post.find('iframe')
        if iframe:
            return iframe.get('src')
