Author: Suthakaran Venkatachalapathy
Role: Data Engineer (Azure | PySpark | ADF | Python)

--> Overview

This project scrapes Business news articles from the Moneycontrol website and stores them in a local SQLite database. The scraper automatically detects links containing “/business/” from the homepage and extracts article details such as title, author, publication date, and content.

This project demonstrates the use of web scraping, HTML parsing, and structured data storage, which are essential components in any ETL or data pipeline process. Each article is extracted with:

Title
Author
Publication Date
Article URL
Content

--> Tech Stack & Tools

Python
BeautifulSoup (bs4)
Requests
SQLite3
Regex (re)
Dateutil.parser
Time

--> Project Structure

WebScraping-Moneycontrol
──> scrape_moneycontrol_to_sqlite.py - Main script
──> articles.db - SQLite database (auto-created)
──> README.md - Information about project

--> Project Flow

flowchart:
A[Start] --> B[Fetch Moneycontrol Homepage] --> C[Collect /business/ Links] --> D[Visit Each Article] --> E[Extract Title, Author, Date, Content] --> F[Clean and Format Data] --> G[Save to SQLite Database] --> H[Repeat for All Links] --> I[End]

--> How to Run the Program

1️⃣ Install Dependencies
Run this once in your terminal:
pip install requests beautifulsoup4 python-dateutil

2️⃣ Run the Script
In your terminal (or VS Code):
python scrape_moneycontrol_to_sqlite.py

3️⃣ Output
The script will:
Fetch the Moneycontrol homepage
Find all “/business/” article links
Extract title, author, date, and content
Save all data into the SQLite database “articles.db”

--> Output Details

Output File: articles.db
Table Name: business_articles

Column Description
id - Unique article ID (auto-increment)
title - Title of the article
author - Author of the article (if available)
publication_date - Date and time of publication
article_url - Article link
content - Full article text

--> Sample Output

id title author publication_date
1 RBI keeps repo rate unchanged Ritu Jha 2025-11-11T10:30:00
2 Markets end flat amid volatility Moneycontrol Bureau 2025-11-12T09:10:00

--> Key Learnings

Building an end-to-end data ingestion pipeline using Python
Parsing and cleaning real-time web data
Working with SQLite for structured storage
Handling inconsistent and missing fields
Practicing polite web scraping with controlled delays

--> Notes

The scraper focuses on Moneycontrol’s Business section.
Selectors may require updates if website structure changes.
Duplicate links are automatically skipped during insertion.

--> End Result

After running the script, a local database file “articles.db” will be created containing all recent Business news articles from Moneycontrol, ready for use in analytics or data processing pipelines.