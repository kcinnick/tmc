#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tmc` package."""
import requests
from bs4 import BeautifulSoup
from tmc.forum_scraper import ForumScraper
from tmc.database import TMCDatabase
from tmc.post import Post, Thread
from tmc.user import User
import pytest


def test_user_build():

    r = requests.get('https://teslamotorsclub.com/tmc/threads/model-s-delivery-update.9489/#post-167939')
    page = BeautifulSoup(r.content, 'html.parser')
    post = page.find('article', id='js-post-175666')
    user = User()
    user._build(post=post)

    assert user.username == 'Chickenlittle'
    assert user.joined == 'Sep 10, 2013'
    assert user.location == 'Virginia'


def test_media_post_collect():
    thread_title = 'test_media_post_collect method'
    with open('fixtures/single_media_post.html', 'r') as f:
        post = BeautifulSoup(f.read(), 'html.parser')
        p = Post(post, thread_title)
        print(vars(p))

    assert p.id == 3463146
    assert p.username == 'gavine'
    assert p.media == 'https://www.youtube.com/embed/IsO3QiCR6_g?wmode=opaque'
    assert p.likes == 10
    assert p.loves == 1


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
    with open('tmc/credentials.txt', 'r') as f:
        api_key = f.readlines()[-1].strip()
    post.get_sentiment(google_api_key=api_key)
    assert post.sentiment['documentSentiment']['magnitude'] == 0.5


def test_scrape_recent_posts():
    forum_scraper = ForumScraper()
    recent_posts = forum_scraper.scrape_recent_posts(pages=2)
    assert len(recent_posts) == 50


def test_clean_message():
    forum_scraper = ForumScraper()
    post = forum_scraper.scrape_post_by_id(post_id=3741808)
    assert post.message.startswith('My mistake, you have my apologies.')
    assert post.reply_ids == ['3741789']


@pytest.mark.skip(reason="Skipped by default b/c it will fail if DB and credentials aren't present.")
def test_retrieve_posts_from_database():
    with open('tmc/credentials.txt', 'r') as f:
        password = f.readlines()[0].strip()

    import pymysql
    connection = pymysql.connect(
        user='root', password=password,
        host='127.0.0.1',
        database='tmc',
    )
    tmc_database = TMCDatabase(connection)
    posts = tmc_database.retrieve_from_posts_database(from_post_id=1, to_post_id=10, attrs='*', limit=8)
    assert len(posts) == 8


@pytest.mark.skip(reason="Skipped by default b/c it will fail if DB and credentials aren't present.")
def test_export_to_csv():
    with open('tmc/credentials.txt', 'r') as f:
        password = f.read().strip()

    import pymysql
    connection = pymysql.connect(
        user='root', password=password,
        host='127.0.0.1',
        database='tmc',
    )
    tmc_database = TMCDatabase(connection)
    tmc_database.export_to_csv(file_name='test.csv', from_post_id=0, to_post_id=10, attrs='*')


@pytest.mark.skip(reason="Skipped by default b/c it will fail if DB and credentials aren't present.")
def test_build_post_from_db():
    # TODO: write test!
    return
