from tmc.forum_scraper import TMCDatabase
import pymysql

with open('credentials.txt', 'r') as f:
    password = f.read().strip()

connection = pymysql.connect(
    user='root', password=password,
    host='127.0.0.1',
    database='tmc',
)
tmc_database = TMCDatabase(connection)
tmc_database.export_to_csv(file_name='0_10000.csv', from_post_id=0, to_post_id=10000, attrs='*')
