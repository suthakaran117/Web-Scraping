'''
import sqlite3
conn = sqlite3.connect("articles.db")
for row in conn.execute("SELECT id,title,author,publication_date,article_url FROM business_articles LIMIT 20"):
    print(row)
conn.close()
'''

import sqlite3

conn = sqlite3.connect("articles.db")
cur = conn.cursor()

cur.execute("SELECT id, title, author, publication_date, article_url FROM business_articles LIMIT 20")
rows = cur.fetchall()

for r in rows:
    print(f"ID: {r[0]}\nTitle: {r[1]}\nAuthor: {r[2]}\nDate: {r[3]}\nURL: {r[4]}\n{'-'*80}")

conn.close()
