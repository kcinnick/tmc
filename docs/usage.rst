=====
Usage
=====

To use tmc in a project::

    from forum_scraper import ForumScraper, Post
    import pymysql
    from time import sleep


    def upload_recent_posts():
        forum_scraper = ForumScraper()
        connection = pymysql.connect(
        user='root', password='yourpassword',
        host='127.0.0.1',
        database='yourdatabase')

    forum_scraper.scrape_recent_posts(db_connection=connection)
