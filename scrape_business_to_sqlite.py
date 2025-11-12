#!/usr/bin/env python3
"""
scrape_moneycontrol_to_sqlite.py

A simple Python script to scrape the Moneycontrol homepage for
links that belong to the Business section (those containing '/business/')
and store the article data (title, author, date, content) in a local
SQLite database called 'articles.db'.

Usage:
    python scrape_moneycontrol_to_sqlite.py
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urljoin, urlparse
import time
import sys
from dateutil import parser as dateparser
import re

# ---------------------------
# basic configuration
# ---------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/117.0 Safari/537.36"
}
DB_PATH = "articles.db"
TABLE_NAME = "business_articles"
REQUEST_SLEEP = 0.8                                         # short delay between article requests


# ---------------------------
# Database setup helpers
# ---------------------------
def create_db():
    """Create the SQLite DB and table if not already present."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            publication_date TEXT,
            article_url TEXT UNIQUE,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

# save article to database
def save_article_to_db(article):
    """Insert a single article into the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute(f"""
            INSERT INTO {TABLE_NAME} (title, author, publication_date, article_url, content)
            VALUES (?, ?, ?, ?, ?)
        """, (
            article.get("title"),
            article.get("author"),
            article.get("publication_date"),
            article.get("article_url"),
            article.get("content")
        ))
        conn.commit()
        print(f"[DB] Saved: {article.get('title')[:60]}")
    except sqlite3.IntegrityError:
        # this happens if the article URL already exists
        print(f"[DB] Skipped (duplicate): {article.get('article_url')}")
    except Exception as e:
        print(f"[DB] Error saving article: {e}")
    finally:
        conn.close()


# HTTP utilities to get BeautifulSoup objects

def get_soup(url):
    """Fetch a webpage and return a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=12)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"[HTTP] Failed to fetch {url}: {e}")
        return None

# date parsing function

def parse_iso_datetime(text):
    """Try to parse any date string and return it in ISO format."""
    if not text:
        return None
    try:
        dt = dateparser.parse(text)
        return dt.isoformat()
    except Exception:
        return text.strip()

# text extraction helper
def extract_text_from_elements(elements):
    """Extract plain text from multiple HTML elements and join them nicely."""
    chunks = []
    for el in elements:
        txt = el.get_text(separator=" ", strip=True)
        if txt:
            chunks.append(txt)
    return "\n\n".join(chunks).strip()


# Main parser for Moneycontrol articles

def parse_moneycontrol(url, soup):
    """Extract title, author, date, and main content from a Moneycontrol article."""
    out = {
        "article_url": url,
        "title": None,
        "author": None,
        "publication_date": None,
        "content": None
    }

    # Title: usually in og:title or h1
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        out["title"] = og_title["content"].strip()
    if not out["title"]:
        h1 = soup.find("h1")
        if h1:
            out["title"] = h1.get_text(strip=True)

    # Author: try meta first, then visible bylines
    meta_author = soup.find("meta", {"name": "author"})
    if meta_author and meta_author.get("content"):
        out["author"] = meta_author["content"].strip()
    else:
        author_sel = soup.select_one(".author, .byline, .author-name, .article-author, a[rel='author']")
        if author_sel:
            out["author"] = author_sel.get_text(separator=" ", strip=True)
        else:
            # sometimes it's plain text starting with "By ..."
            by_text = soup.find(string=re.compile(r"^By\s+", re.I))
            if by_text and by_text.parent:
                out["author"] = by_text.parent.get_text(separator=" ", strip=True)

    # Publication date: check meta first, then time tags, then generic date spans
    meta_pub = soup.find("meta", property="article:published_time")
    if meta_pub and meta_pub.get("content"):
        out["publication_date"] = parse_iso_datetime(meta_pub["content"])
    else:
        time_tag = soup.find("time")
        if time_tag:
            dt = time_tag.get("datetime") or time_tag.get_text()
            out["publication_date"] = parse_iso_datetime(dt)
        else:
            date_el = soup.select_one(".date, .time, .publishing-date, .article-date")
            if date_el:
                out["publication_date"] = parse_iso_datetime(date_el.get_text())

    # Possible locations where article text appears
    content_selectors = [
        "div.articleText",
        "div.articleContent",
        "div.article-desc",
        "div#content",
        "div#articleBody",
        "article"
    ]
    content = None
    for sel in content_selectors:
        node = soup.select_one(sel)
        if node:
            paragraphs = node.find_all(["p", "div"], recursive=True)
            content = extract_text_from_elements(paragraphs)
            if content:
                break

    # Fallback: look for <article> or all <p> tags
    if not content:
        article_tag = soup.find("article")
        if article_tag:
            content = extract_text_from_elements(article_tag.find_all("p"))
    if not content:
        all_p = soup.find_all("p")
        content = extract_text_from_elements(all_p)

    out["content"] = content or ""
    return out


# Collect Business article links from homepage

def collect_business_links(home_url, homepage_soup):
    """Find and return all same-site /business/ article links from homepage."""
    parsed_home = urlparse(home_url)
    base_netloc = parsed_home.netloc
    links = set()

    for a in homepage_soup.find_all("a", href=True):
        href = a["href"].strip()
        abs_url = urljoin(home_url, href)
        parsed = urlparse(abs_url)

        # skip external domains
        if parsed.netloc != base_netloc:
            continue

        # only keep URLs containing '/business/'
        if "/business/" in parsed.path:
            cleaned = abs_url.split("#")[0].split("?")[0]
            links.add(cleaned)

    return links


# Main scraping workflow
def scrape_moneycontrol():
    home_url = "https://www.moneycontrol.com/"
    print(f"[INFO] Fetching homepage: {home_url}")

    homepage_soup = get_soup(home_url)
    if not homepage_soup:
        print("[ERROR] Failed to load Moneycontrol homepage.")
        return

    links = collect_business_links(home_url, homepage_soup)
    print(f"[INFO] Found {len(links)} Business links (filtered by '/business/').")

    if not links:
        print("[INFO] No Business section links found, exiting.")
        return

    create_db()

    for idx, link in enumerate(sorted(links)):
        print(f"\n[SCRAPE] ({idx + 1}/{len(links)}) {link}")
        soup = get_soup(link)
        if not soup:
            print("[WARN] Couldnt fetch page, skipping.")
            continue

        try:
            article = parse_moneycontrol(link, soup)
            if not article.get("title") and not article.get("content"):
                print("[WARN] No title/content found — probably not a news article.")
                continue
            save_article_to_db(article)
        except Exception as e:
            print(f"[ERROR] Failed to parse {link}: {e}")

        time.sleep(REQUEST_SLEEP)

# call the main function
if __name__ == "__main__":
    scrape_moneycontrol()
    print("\nDone. DB file:", DB_PATH)
    print(f"Table: {TABLE_NAME} (view it using sqlite3 or DB Browser).")
