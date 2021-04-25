from bs4 import BeautifulSoup

from tqdm import tqdm

from tmc.post import Post, Thread
from pymysql.err import IntegrityError
import requests
import re


class ForumScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'https://github.com/kcinnick/tmc'})

    @staticmethod
    def get_number_of_pages_in_thread(soup: BeautifulSoup):
        """
        Retrieves the number of pages in a thread.
        """

        nav_header = soup.find('span', class_='pageNavHeader')

        if nav_header:
            return int(soup.find('span', class_='pageNavHeader').text.split()[-1])
        else:
            return 1

    def scrape_recent_posts(self, pages: int = 10, db_connection=None):
        """
        Scrapes most recent posts as shown by https://teslamotorsclub.com/tmc/recent-posts/
        and returns post objects for each new post. Only returns 10 pages worth of posts.
        """

        url = 'https://teslamotorsclub.com/tmc/recent-posts/'
        if not db_connection:
            print('DB connection info not found.\n')
        recent_posts = []
        integrity_errors = 0
        for page_number in tqdm(range(1, pages + 1)):
            recent_posts_url = url + f'?page={page_number}'
            response = self.session.get(recent_posts_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            try:
                discussion_list_items = soup.find('ol', class_='discussionListItems').find_all('dl', class_='lastPostInfo')
            except AttributeError as e:
                print('Error: {}'.format(e))
                print(recent_posts_url)
            for post in discussion_list_items:
                post_id = post.find('a').get('href')[6:-1]
                post_url = 'https://teslamotorsclub.com/tmc/posts/' + post_id
                post_response = self.session.get(post_url)
                post_soup = BeautifulSoup(post_response.content, 'html.parser')
                targeted_post = post_soup.find('li', attrs={'id': f'fc-post-{post_id}'})
                thread_title = post_soup.find('div', class_='titleBar').text.strip().split('\n')[0]
                parsed_post = Post(targeted_post, thread_title)
                if db_connection:
                    try:
                        parsed_post.upload_to_db(db_connection)
                        print(f'Post {post_id} uploaded.\n')
                    except IntegrityError:
                        integrity_errors += 1
                        print('Duplicate found - ignoring.\n')
                        #if integrity_errors > 11:
                        #    print('Old data reached - stopping search.')
                        #    return
                        # Commented this out because this may not be desired behavior
                        # given that recent-posts only returns 10 pages worth of posts.
                recent_posts.append(parsed_post)


        return recent_posts

    def scrape_post_by_id(self, post_id: int = 0):
        """
        Given a post or thread's ID, retrieves the post's URL
        and returns a Post object.
        """

        url = f'https://teslamotorsclub.com/tmc/posts/{post_id}/'
        print('\n', url)
        response = self.session.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')

        thread_title = soup.find('meta', attrs={'property': 'og:title'}).get('content')
        unparsed_post = soup.find('article', attrs={'id': re.compile(f'js-post-{post_id}')})

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
            unparsed_posts = [i for i in soup.find_all('article') if i.get('data-author')]
            print(f"{len(unparsed_posts)} posts found.\n")
            thread_title = soup.find('meta', {"property": "og:title"}).get('content')
            print(f'Scraping thread: "{thread_title}" at {url}')

            for post in unparsed_posts:
                p = Post(post, thread_title)
                posts.append(p)

        return posts

    def search_threads_and_posts(self, keywords: list, posted_by: list, newer_than: str,
                                 minimum_replies: int, thread_prefixes: list,
                                 search_in_forums: list, search_child_forums: bool,
                                 most_recent: bool = False, most_replies: bool = False):
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

        r = self.session.get('https://teslamotorsclub.com/tmc/search/?type=post')
        soup = BeautifulSoup(r.content, 'html.parser')
        form_data['_xfToken'] = soup.find('input', attrs={'name': '_xfToken'}).get('value')

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

        try:
            pages = soup.find('a', class_='PageNavNext').find_next('a').text
        except AttributeError:
            pages = 2

        search_results = []

        for page in range(1, int(pages)):
            if page != 1:
                url = redirect_target + f'&page={page}'
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')

            search_results_list = soup.find('ol', class_='searchResultsList').find_all('li')
            for search_result in search_results_list:
                if 'thread' in search_result.get('class'):
                    title = search_result.find('h3', class_='title').text
                    thread_id = search_result.find('h3', class_='title').find('a').get('href')
                    thread = Thread(title, self.scrape_post_by_id(thread_id=thread_id))
                    #  What is going on here? Raises unexpected keyword arg here
                    #  Figure this out and return to it. Where was this introduced?
                    search_results.append(thread)
                else:
                    post_id = search_result.find('h3', class_='title').find('a').get('href')
                    post_id = post_id[6:-1]
                    post = self.scrape_post_by_id(post_id=post_id)
                    search_results.append(post)

        return search_results
