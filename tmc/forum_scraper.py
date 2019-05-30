from bs4 import BeautifulSoup, Tag
import datetime
from pymysql.err import IntegrityError
import requests
import re


class User:
    def __init__(self):
        self.username = None
        self.member_type = None
        self.joined = None
        self.messages = None
        self.location = None

    def get_info(self, post: Tag = None, url: str = None):
        """
        Retrieves basic user information.
        TODO: Add logic for parsing from URL.
        """

        if post:
            user_info = post.find('div', class_='messageUserInfo')
            self.username = user_info.find('a', class_='username').text
            self.member_type = user_info.find('em', class_='userTitle').text

            extra_user_info = {i.text[:-1]: i.find_next('dd').text.strip() for i in post.find_all('dt')}
            self.joined = extra_user_info['Joined']
            self.messages = ([], extra_user_info['Messages'])
            self.location = extra_user_info['Location']


class Post:
    def __init__(self, post: Tag, thread_title: str):
        self.id = int(post.find('a', class_='datePermalink').get('href').split('/')[1])
        self.thread_title = thread_title.replace("'", "\\'").replace('"', '\\"').split('Discussion in ')[0].strip()
        self.username = post.find('div', class_='messageUserInfo').find('a', class_='username').text
        try:
            self.posted_at = post.find('span', class_='DateTime').text
        except AttributeError:  # sometimes posted_at is hidden behind an abbr tag
            self.posted_at = post.find('abbr', class_='DateTime').text
        try:
            self.posted_at = datetime.datetime.strptime(self.posted_at, '%b %d, %Y at %I:%M %p')
        except ValueError:
            self.posted_at = post.find('span', class_='DateTime').get('title')
            self.posted_at = datetime.datetime.strptime(self.posted_at, '%b %d, %Y at %I:%M %p')
        self.message = post.find('div', class_='messageContent').text.replace('â†‘', '\n"').replace(
            'Click to expand...', '\n"').strip()
        self.media = self.get_media(post)

        output_list = post.find('ul', class_='dark_postrating_outputlist')
        output_dict = self.parse_output_list(output_list)

        self.likes = output_dict.get('Like', 0)
        self.loves = output_dict.get('Love', 0)
        self.helpful = output_dict.get('Helpful', 0)

        self.sentiment = 0

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

    def get_sentiment(self, session=requests.Session()):
        """
        Gets sentiment data of post.
        """

        r = session.post('http://text-processing.com/api/sentiment/',
                         data={'text': self.message})
        self.sentiment = r.json()

    def upload_to_db(self, db_connection):
        message = self.message.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        sql_statement = "INSERT INTO `posts` (`id`, `thread_title`, `username`, `posted_at`, `message`, `likes`, "
        sql_statement += f"`loves`, `helpful`, `sentiment`) VALUES ('{self.id}', '{self.thread_title}', "
        sql_statement += f"'{self.username}', '{self.posted_at}', '{message}',"
        sql_statement += f"{self.likes}, {self.loves}, {self.helpful}, {self.sentiment})"
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
        and returns post objects for each new post.
        """

        url = 'https://teslamotorsclub.com/tmc/recent-posts/'

        recent_posts = []
        integrity_errors = 0
        for page_number in range(1, pages):
            recent_posts_url = url + f'?page={page_number}'
            response = self.session.get(recent_posts_url)
            soup = BeautifulSoup(response.content, 'html.parser')
            discussion_list_items = soup.find('ol', class_='discussionListItems')
            for post in discussion_list_items.find_all('dl', class_='lastPostInfo'):
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
                        print('Post uploaded, moving on.\n')
                    except IntegrityError:
                        integrity_errors += 1
                        print('Duplicate found - ignoring.\n')
                        if integrity_errors > 11:
                            print('Old data reached - stopping search.')
                            return
                recent_posts.append(parsed_post)

        return recent_posts

    def scrape_post_by_id(self, post_id: int = 0):
        """
        Given a post or thread's ID, retrieves the post's URL
        and returns a Post object.
        """

        url = f'https://teslamotorsclub.com/tmc/posts/{post_id}/'

        response = self.session.get(url)

        soup = BeautifulSoup(response.content, 'html.parser')

        thread_title = soup.find('div', class_='titleBar').text.strip()
        unparsed_post = soup.find('li', attrs={'id': re.compile(f'fc-post-{post_id}')})

        if 'The requested post could not be found.' in soup.text:
            raise ValueError
        elif 'The requested thread could not be found.' in soup.text:
            raise ValueError
        elif 'Tesla Motors Club - Error' in soup.text:
            raise ValueError
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
        number_of_pages = self.get_number_of_pages_in_thread(soup)

        for page_number in range(0, number_of_pages):
            page_number += 1
            if page_number == 1:
                pass
            else:
                response = self.session.get(url + f'page-{page_number}')
                soup = BeautifulSoup(response.content, 'html.parser')

            unparsed_posts = soup.find_all('li', attrs={'id': re.compile('fc-post-\d+')})
            thread_title = soup.find('div', class_='titleBar').text.strip().split('\n')[0]

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
                    search_results.append(thread)
                else:
                    post_id = search_result.find('h3', class_='title').find('a').get('href')
                    post_id = post_id[6:-1]
                    post = self.scrape_post_by_id(post_id=post_id)
                    search_results.append(post)

        return search_results


class TMCDatabase:
    def __init__(self, connection):
        self.connection = connection

    def retrieve_from_posts_database(self, from_post_id=None, to_post_id=None, limit=None, attrs='*'):
        import pymysql
        sql_statement = f"SELECT {attrs} FROM posts WHERE "
        if from_post_id:
            sql_statement += f"POST ID > f{from_post_id} "
            if to_post_id:
                sql_statement += f"< {to_post_id}"
        if limit:
            sql_statement += f" LIMIT {limit}"
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            results = cursor.fetchall()
            return results

