#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tmc` package."""
import os

import pytest
import requests
from bs4 import BeautifulSoup
from tmc.forum_scraper import ForumScraper
from tmc.database import TMCDatabase
from tmc.post import Post
from tmc.user import User


def get_session():
    session = requests.Session()
    session.headers.update({'User-Agent': 'https://github.com/kcinnick/tmc'})
    return session


def test_user_build():
    session = get_session()
    r = session.get(
        'https://teslamotorsclub.com/tmc/threads/model-s-delivery-update.'
        '9489/#post-167939')
    page = BeautifulSoup(r.content, 'html.parser')
    post = page.find('article', id='js-post-175666')
    user = User()
    user._build(post=post)

    assert user.username == 'Thread Summary'
    assert user.joined == 'Aug 14, 2012'
    assert user.location is None


def test_media_post_collect():
    thread_title = 'test_media_post_collect method'
    session = get_session()
    r = session.get(
        'https://teslamotorsclub.com/tmc/threads/tip-how-to-open-your-'
        'charge-port-with-a-key-fob.91313/#post-2119568')
    page = BeautifulSoup(r.content, 'html.parser')
    post = page.find('article', id='js-post-2119568')
    p = Post(post, thread_title)

    assert p.id == 2119568
    assert p.username == 'AlexG'
    assert p.media == (
        'https://www.youtube.com/embed/dS4y-rlp9qA?wmode=opaque&start=0')
    assert p.likes == 0
    assert p.loves == 0


def test_scrape_posts_from_thread():
    forum_scraper = ForumScraper()
    url = 'https://teslamotorsclub.com/tmc/threads/i-thought-i-woul'
    url += 'd-mention-that-i-think-tesla-has-one-of-the-nicest-websites.14'
    print(url)
    posts = forum_scraper.scrape_posts_from_thread(url=url)
    assert len(posts) == 4


def test_scrape_specific_post_from_thread():
    forum_scraper = ForumScraper()

    post = forum_scraper.scrape_post_by_id(post_id=3508669)

    assert post.id == 3508669
    assert post.username == 'InParadise'
    assert 'Do you have a referral' in post.message


def test_search_threads_and_posts():
    forum_scraper = ForumScraper()
    search_results = forum_scraper.search_threads_and_posts(
        keywords=['tires', 'spike'], posted_by=[], newer_than=None,
        minimum_replies=None, thread_prefixes=[],
        search_in_forums=[], search_child_forums=False,
        most_recent=True, most_replies=False)

    assert len(search_results) > 40


def test_message_get_sentiment():
    forum_scraper = ForumScraper()

    post = forum_scraper.scrape_post_by_id(post_id=3507092)
    api_key = os.getenv('google_api_key', None)
    if not api_key:
        print('No API key found. Returning. \n')
        return
    post.get_sentiment(google_api_key=api_key)

    assert post.sentiment['documentSentiment']['magnitude'] == 0.6


def test_scrape_recent_posts():
    forum_scraper = ForumScraper()
    recent_posts = forum_scraper.scrape_recent_posts(pages=2)
    assert len(recent_posts) == 40


def test_clean_message():
    forum_scraper = ForumScraper()
    post = forum_scraper.scrape_post_by_id(post_id=3741808)
    assert post.message.startswith('My mistake, you have my apologies.')
    assert post.reply_ids == ['3741789']


skip_db_test_reason = (
    'Skipped by default b/c it will fail if DB and credentials aren\'t'
    'present.'
)


@pytest.mark.skipif(
    not os.getenv('TMC_CREDENTIALS'),
    reason=skip_db_test_reason)
def test_retrieve_posts_from_database():
    tmc_credentials = os.getenv('TMC_CREDENTIALS')

    import pymysql
    connection = pymysql.connect(
        user='nick', password=tmc_credentials,
        host='127.0.0.1',
        database='tmc',
    )
    tmc_database = TMCDatabase(connection)
    posts = tmc_database.retrieve_from_posts_database(
        attrs='*', limit=8, debug=True)
    assert len(posts) == 8


@pytest.mark.skipif(
    not os.getenv('TMC_CREDENTIALS'),
    reason=skip_db_test_reason)
def test_export_to_csv():
    tmc_credentials = os.getenv('TMC_CREDENTIALS')
    import pymysql
    connection = pymysql.connect(
        user='nick', password=tmc_credentials,
        host='127.0.0.1',
        database='tmc',
    )
    tmc_database = TMCDatabase(connection)
    tmc_database.export_to_csv(
        file_name='test.csv', from_post_id=0, to_post_id=10, attrs='*')


@pytest.mark.skipif(
    not os.getenv('TMC_CREDENTIALS'),
    reason=skip_db_test_reason)
def test_build_post_from_db():
    # TODO: write test!
    return
