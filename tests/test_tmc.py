#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `tmc` package."""

from bs4 import BeautifulSoup
from tmc.forum_scraper import User, Post, ForumScraper
import pytest

def test_user_collection():
    with open('tests/fixtures/single_post.html', 'r') as f:
        post = BeautifulSoup(f.read(), 'html.parser')
        user = User()
        user.get_info(post=post)

    assert user.username == 'Chickenlittle'
    assert user.joined == 'Sep 10, 2013'
    assert user.location == 'Virginia'

def test_media_post_collect():
    with open('tests/fixtures/single_media_post.html', 'r') as f:
        post = BeautifulSoup(f.read(), 'html.parser')
        p = Post(post)
    
    assert p.id == 3463146
    assert p.username == 'gavine'
    assert p.media == 'https://www.youtube.com/embed/IsO3QiCR6_g?wmode=opaque'
    assert p.likes == 10
    assert p.loves == 1

def test_scrape_posts_from_thread():
    forum_scraper = ForumScraper()

    posts = forum_scraper.scrape_posts_from_thread(url='https://teslamotorsclub.com/tmc/threads/i-thought-i-would-mention-that-i-think-tesla-has-one-of-the-nicest-websites.14/')
    assert len(posts) == 4