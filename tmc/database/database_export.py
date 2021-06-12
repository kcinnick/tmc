import os

from tmc.forum_scraper import TMCDatabase
import pymysql

tmc_credentials = os.getenv('TMC_CREDENTIALS')

connection = pymysql.connect(
    user='root', password=tmc_credentials,
    host='127.0.0.1',
    database='tmc',
)
tmc_database = TMCDatabase(connection)
tmc_database.export_to_csv(file_name='0_10000.csv', from_post_id=0, to_post_id=10000, attrs='*')
