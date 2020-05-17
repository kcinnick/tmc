from csv import DictWriter
import datetime
from tmc.forum_scraper import ForumScraper
from tmc.post import Post
from pymysql.cursors import DictCursor


class TMCDatabase:
    def __init__(self, connection):
        self.connection = connection

    def retrieve_from_posts_database(self, debug=False, attrs='*', build=True, **kwargs):
        keys = kwargs.keys()
        if 'attrs' not in keys:
            kwargs['attrs'] = attrs
        sql_statement = f"SELECT {kwargs['attrs']} FROM posts WHERE "
        if 'from_post_id' in keys:
            sql_statement += f"`id` > {kwargs['from_post_id']} "
            if 'to_post_id' in keys:
                sql_statement += f"AND `id` < {kwargs['to_post_id']}"
        if 'posted_at_start' in keys:
            sql_statement += f"`posted_at` > '{kwargs['posted_at_start']}'"
            if 'posted_at_end' in keys:
                sql_statement += f" AND `posted_at` < '{kwargs['posted_at_end']}'"
        if 'in_reply_to' in keys:
            sql_statement += f"`in_reply_to` = '{kwargs['in_reply_to']}'"
        if 'id' in keys:
            if sql_statement.endswith('\''):
                sql_statement += ' AND '
            sql_statement += f"`id` = {kwargs['id']}"
        if 'limit' in keys:
            sql_statement += f" LIMIT {kwargs['limit']}"
        if debug:
            print(sql_statement)
        with self.connection.cursor(DictCursor) as cursor:
            cursor.execute(sql_statement)
            results = cursor.fetchall()
            parsed_results = []
            for result in results:
                if build:
                    result = Post(db_entry=result)
                parsed_results.append(result)
            return parsed_results

    def export_to_csv(self, **kwargs):
        keys = kwargs.keys()
        assert 'file_name' in keys
        posts = self.retrieve_from_posts_database(**kwargs)
        with open(kwargs['file_name'], 'w', newline='\n', encoding='utf-8') as csvfile:
            field_names = ['id', 'thread_title', 'username', 'posted_at', 'message', 'media', 'likes', 'loves',
                           'helpful', 'sentiment']
            writer = DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(posts)

    def id_gaps_in_scraped_post(self):
        #  Useful for historical DB building.
        #  Assumes up to date recent posts.
        sql_statement = "SELECT `id` FROM posts"
        with self.connection.cursor() as cursor:
            cursor.execute(sql_statement)
            results = cursor.fetchall()
            last_post_id = results[-1][-1]
            results = set([i[0] for i in results])
            list_of_possible_values = set(range(1, last_post_id + 1))
            outstanding_posts = [post_id for post_id in list_of_possible_values if post_id not in results]
            return outstanding_posts

    def retrieve_posts_for_timeframe(self, posted_at_start, posted_at_end, debug=False):
        results = self.retrieve_from_posts_database(
            posted_at_start=posted_at_start, posted_at_end=posted_at_end, debug=debug)

        return results

    def graph_amount_of_posts_for_daterange(self, skip=1, **kwargs):
        #  Abstract this out a bit for the future
        #  Think sentiment graphing, etc.
        import pandas as pd
        import matplotlib.pyplot as plt

        datelist = pd.date_range(kwargs['start_date'], periods=kwargs['periods']).to_pydatetime().tolist()
        results = []
        dates = []
        with self.connection.cursor() as cursor:
            for date in datelist:
                sql_statement = "SELECT COUNT(*) FROM POSTS WHERE `posted_at` > '{0}' AND `posted_at` < '{1}'".format(
                    date.strftime('%Y-%m-%d 00:00:00'), (date + datetime.timedelta(days=skip)).strftime('%Y-%m-%d 00:00:00')
                )
                dates.append(date.strftime('%Y-%m-%d'))
                cursor.execute(sql_statement)
                results.append(cursor.fetchone()[0])

        plt.plot(dates, results)
        plt.ylabel('posts')
        plt.xlabel('dates')
        plt.show()
        return

    def alter_records_to_include_in_reply_to(self, limit=100, debug=False):
        """
        When this database was originally written, there hadn't been a final decision
        made about how to handle posts in reply to other posts.  With sentiment analysis
        it's become clear that a way to handle these posts is necessary and thus the records
        entered prior to that decision being made need to be altered to conform to the new
        schema.
        """
        if limit:
            post_ids = self.retrieve_from_posts_database(attrs='(`id`)', in_reply_to='tbd', build=False, limit=limit)
        else:
            post_ids = self.retrieve_from_posts_database(attrs='(`id`)', in_reply_to='tbd', build=False)

        forum_scraper = ForumScraper()
        for post_id in reversed(post_ids):
            try:  #  THIS IS A TEMPORARY SOLUTION!
                  #  DEAL WITH THIS ASAP!
                post = forum_scraper.scrape_post_by_id(post_id=post_id['id'])
            except ValueError:
                continue
            if debug:
                print(post_id)
            sql_statement = "UPDATE `posts` SET `message` = '{}', `in_reply_to` = '{}' WHERE `id` = {}".format(
                post.message.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n'),
                str(','.join(post.reply_ids)),
                post_id['id']
            )
            with self.connection.cursor() as cursor:
                cursor.execute(sql_statement)
                self.connection.commit()
        return
