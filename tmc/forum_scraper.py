import os

import pymysql
from bs4 import BeautifulSoup

from tqdm import tqdm

from tmc.database import TMCDatabase
from tmc.post import Post, Thread
import requests
import re


class ForumScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {'User-Agent': 'https://github.com/kcinnick/tmc'})

    @staticmethod
    def get_number_of_pages_in_thread(soup: BeautifulSoup):
        """
        Retrieves the number of pages in a thread.
        """

        nav_header = soup.find('span', class_='pageNavHeader')

        if nav_header:
            return int(
                soup.find('span', class_='pageNavHeader').text.split()[-1])
        else:
            return 1

    def scrape_recent_posts(self, pages: int = 10, db_connection=None):
        """
        Scrapes most recent posts as shown by
        https://teslamotorsclub.com/tmc/recent-posts/
        and returns post objects for each new post.
        Only returns 10 pages worth of posts.
        """

        url = 'https://teslamotorsclub.com/tmc/whats-new/posts/129206/'
        if not db_connection:
            print('DB connection info not found.\n')
        recent_posts = []
        for page_number in tqdm(range(1, pages + 1)):
            recent_posts_url = url + f'?page-{page_number}'
            response = self.session.get(recent_posts_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            try:
                discussion_list_items = soup.find(
                    'div', class_='structItemContainer'
                ).find_all('div', class_='structItem')
            except AttributeError as e:
                print('Error: {}'.format(e))
                raise e
            for post in discussion_list_items:
                latest_ = post.find(
                    'div', class_='structItem-cell structItem-cell--latest'
                ).find_all('a')
                latest_post_url = (
                    'https://teslamotorsclub.com' + latest_[1].get('href')
                )
                response = self.session.get(latest_post_url)
                post_id = response.url.split('-')[-1]
                post_object = self.scrape_post_by_id(post_id)
                recent_posts.append(post_object)

        return recent_posts

    def scrape_post_by_id(self, post_id: int = 0):
        """
        Given a post or thread's ID, retrieves the post's URL
        and returns a Post object.
        """

        url = f'https://teslamotorsclub.com/tmc/posts/{post_id}/'
        response = self.session.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')

        thread_title = soup.find(
            'meta', attrs={'property': 'og:title'}).get('content')
        unparsed_post = soup.find(
            'article', attrs={'id': re.compile(f'js-post-{post_id}')})

        if 'The requested post could not be found.' in soup.text:
            raise ValueError(post_id)
        elif 'The requested thread could not be found.' in soup.text:
            raise ValueError(post_id)
        elif 'Tesla Motors Club - Error' in soup.text:
            raise ValueError(post_id)
        else:
            return Post(unparsed_post, thread_title)

    def scrape_posts_from_thread(self, url: str = None):
        """
        Parses posts in thread as Post objects and
        returns them in a list.
        """

        posts = []

        response = self.session.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        number_of_pages = self.get_number_of_pages_in_thread(soup) + 1
        for page_number in range(1, number_of_pages):
            if page_number != 1:
                request_url = url + f'page-{page_number}'
                response = self.session.get(request_url)

            soup = BeautifulSoup(response.content, 'html.parser')
            unparsed_posts = [i for i in soup.find_all(
                'article') if i.get('data-author')]
            print(f"{len(unparsed_posts)} posts found.\n")
            thread_title = soup.find(
                'meta', {"property": "og:title"}).get('content')
            print(f'Scraping thread: "{thread_title}" at {url}')

            for post in unparsed_posts:
                p = Post(post, thread_title)
                posts.append(p)

        return posts

    def search_threads_and_posts(
        self, keywords: list, posted_by: list, newer_than: str,
        minimum_replies: int, thread_prefixes: list,
        search_in_forums: list, search_child_forums: bool,
        most_recent: bool = False,
        most_replies: bool = False
    ):
        """
        Behaves the same as the Search Threads and Posts function of TMC:
        https://teslamotorsclub.com/tmc/search/?type=post
        Returns search results, which can be Thread and Post objects.
        """

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

        r = self.session.get(
            'https://teslamotorsclub.com/tmc/search/?type=post')
        soup = BeautifulSoup(r.content, 'html.parser')
        form_data['_xfToken'] = soup.find(
            'input', attrs={'name': '_xfToken'}).get('value')

        if most_recent:
            form_data.update({'order': 'date'})
        else:
            form_data.update({'order': 'replies'})

        response = self.session.post(
            'https://teslamotorsclub.com/tmc/search/search',
            data=form_data, headers={'x-requested-with': 'XmlHttpRequest'})

        redirect_target = response.json().get('redirect')

        if not redirect_target:
            raise ValueError(
                'A redirect target is '
                f'not included in the response: {response.json()}'
            )

        soup = BeautifulSoup(
            self.session.get(redirect_target).content, 'html.parser')

        try:
            pages = soup.find('a', class_='PageNavNext').find_next('a').text
        except AttributeError:
            pages = 2

        search_results = []
        tmc_credentials = os.getenv('TMC_CREDENTIALS')

        connection = pymysql.Connection(user='nick', password=tmc_credentials, )
        db_connection = TMCDatabase(connection)

        for page in range(1, int(pages)):
            if page != 1:
                url = redirect_target + f'&page={page}'
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')

            print(redirect_target)
            search_results_list = soup.find('div', class_='p-body-pageContent'
                                            ).find_all('li')
            for search_result in search_results_list:
                if 'thread' in search_result.get('class', ''):
                    title = search_result.find('h3', class_='title').text
                    thread_id = search_result.find(
                        'h3', class_='title').find('a').get('href')
                    thread = Thread(
                        title, self.scrape_post_by_id(thread_id=thread_id))
                    #  Raises unexpected keyword arg here
                    search_results.append(thread)
                else:
                    try:
                        post_id = search_result.find(
                            'h3', class_='contentRow-title').find(
                            'a').get('href').split('-')[-1]
                        assert post_id.isdigit()
                    except AttributeError:
                        continue
                    except AssertionError:
                        #  thread, not a post
                        continue
                    post = self.scrape_post_by_id(post_id=post_id)
                    search_results.append(post)
                    try:
                        post.upload_to_db(db_connection=db_connection)
                    except pymysql.err.IntegrityError as e:  # duplicate entry
                        print(e)

        return search_results
