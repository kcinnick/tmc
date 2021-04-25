from bs4 import Tag


class User:
    def __init__(self):
        self.username = None
        self.member_type = None
        self.joined = None
        self.messages = None
        self.location = None

    def _build(self, post: Tag = None, url: str = None):
        """
        Retrieves basic user information.
        TODO: Add logic for parsing from URL.
        """
        if post:
            user_info = post.find('div', class_='message-userDetails')
            self.username = user_info.find('a', class_='username').text
            self.member_type = user_info.find('h5', class_='userTitle message-userTitle').text

            extra_user_info = post.find('div', class_='message-userExtras')
            keys = [i.find('span').get('title') for i in extra_user_info.find_all('dt')]
            values = [i.text for i in extra_user_info.find_all('dd')]
            extra_user_info = {keys[i]: values[i] for i in range(len(keys))}

            self.joined = extra_user_info.get('Joined')
            self.messages = ([], extra_user_info.get('Messages'))
            self.location = extra_user_info.get('Location')
        else:
            raise NotImplementedError
