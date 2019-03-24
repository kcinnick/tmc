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

class Thread:
    def __init__(self, title, post):
        super().__init__(post)
        self.title = title

class Post:
    def __init__(self, post):
        self.id = int(post.find('a', class_='datePermalink').get('href').split('/')[1])
        self.username = post.find('div', class_='messageUserInfo').find('a', class_='username').text
        try:
            self.posted_at = post.find('span', class_='DateTime').text
        except AttributeError:
            self.posted_at = post.find('abbr', class_='DateTime').text
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
    
    def scrape_post_by_id(self, post_id: int=0):
        url = f'https://teslamotorsclub.com/tmc/posts/{post_id}/'
        response = self.session.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        unparsed_post = soup.find('li', attrs={'id': re.compile(f'fc-post-{post_id}')})
        return Post(unparsed_post)
    
    def scrape_posts_from_thread(self, url: str=None):
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

    def search_threads_and_posts(self, keywords: list, posted_by: list, newer_than:str,
                                 minimum_replies:int, thread_prefixes:list, search_in_forums:list,
                                 search_child_forums: bool, most_recent:bool, most_replies:bool):
            form_data = {'keywords': ','.join(keywords),
                         'users': ','.join(posted_by),
                         'date': newer_than,
                         'reply_count': minimum_replies,
                         'nodes[]': '',
                         'child_nodes': 1,
                         'type': 'post',
                         '_xfToken': '',
                         '_xfRequestUri': '/tmc/search/?type=post',
                         '_xfNoRedirect': 1,
                         '_xfResponseType': 'json'
                         }
            
            if most_recent:
                form_data.update({'order': 'date'})
            else:
                form_data.update({'order': 'replies'})
            
            response = self.session.post('https://teslamotorsclub.com/tmc/search/search',
            data=form_data, headers={'x-requested-with': 'XmlHttpRequest'})

            redirect_target = response.json().get('_redirectTarget')

            if not redirect_target:
                raise ValueError('A redirect target is not incl' + 
                                 f'uded in the response: {response.json()}'
                )
            
            soup = BeautifulSoup(self.session.get(redirect_target).content, 'html.parser')
            pages = soup.find('a', class_='PageNavNext').find_next('a').text

            for page in range(1, int(pages)):
                if page != 1:
                    url = redirect_target + f'&page={page}'
                    response = self.session.get(url)
                    soup = BeautifulSoup(response.content, 'html.parser')
                
                search_results_list = soup.find('ol', class_='searchResultsList').find_all('li')
            