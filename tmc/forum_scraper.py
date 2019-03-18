from bs4 import BeautifulSoup
import requests
import re

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
        output_dict = self.parse_output_list(output_list)

        self.likes = output_dict.get('Like', 0)
        self.loves = output_dict.get('Love', 0)
        self.helpful = output_dict.get('Helpful', 0)

    def parse_output_list(self, output_list):
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

    def get_media(self, post):
        iframe = post.find('iframe')
        if iframe:
            return iframe.get('src')

class ForumScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'https://github.com/kcinnick/tmc'})
    
    def get_number_of_pages_in_thread(self, soup: BeautifulSoup):
        nav_header = soup.find('span', class_='pageNavHeader')
        
        if nav_header:
            return int(soup.find('span', class_='pageNavHeader').text.split()[-1])
        else:
            return 1
    
    def scrape_posts_from_thread(self, url: str):
        posts = []

        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        number_of_pages = self.get_number_of_pages_in_thread(soup)

        for page_number in range(0, number_of_pages):
            page_number += 1
            if page_number == 1:
                pass
            else:
                response = self.session.get(url + f'page-{page_number}')
                soup = BeautifulSoup(response.content, 'html.parser')
            
            unparsed_posts = soup.find_all('li', attrs={'id': re.compile('fc-post-\d+')})
            for post in unparsed_posts:
                p = Post(post)
                posts.append(p)
        
        return posts
