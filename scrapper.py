import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import hashlib

def fetch_articles(url):
    r = requests.get(url)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    articles = []

    # Riot patch cards
    cards = soup.select("a[data-testid='articlefeaturedcard-component']")
    if not cards:
        # fallback for single patch page (Valorant or LoL main patch)
        cards = [soup]

    for card in cards:
        title_el = card.select_one("div[data-testid='card-title'], h1")
        title = title_el.get_text(strip=True) if title_el else "Sin título"

        time_el = card.select_one("div[data-testid='card-date'] time, time")
        pub_date = time_el["datetime"] if time_el and time_el.has_attr("datetime") else datetime.utcnow().isoformat()

        card_img_el = card.select_one("img[data-testid='mediaImage'], div[data-testid='article-hero-image'] img")
        card_img_url = card_img_el['src'] if card_img_el and card_img_el.has_attr('src') else ""

        href = card.get("href") if card.get("href") else url
        if href.startswith("/"):
            href = "https://www.leagueoflegends.com" + href

        # fetch patch detail
        desc = ""
        detail_img_url = card_img_url
        try:
            detail_resp = requests.get(href)
            detail_resp.raise_for_status()
            detail_soup = BeautifulSoup(detail_resp.text, "lxml")

            resume_div = detail_soup.select_one("div.white-stone div, div[data-testid='content']")
            if resume_div:
                p_el = resume_div.select_one("p")
                desc = p_el.get_text(strip=True) if p_el else ""
                img_el = resume_div.select_one("img")
                if img_el and img_el.has_attr('src'):
                    detail_img_url = img_el['src']
        except Exception as e:
            print(f"Failed to fetch detail page {href}: {e}")

        articles.append({
            "title": title,
            "link": href,
            "description": desc,
            "pubDate": pub_date,
            "guid": hashlib.md5(href.encode()).hexdigest(),
            "image": detail_img_url
        })

    return articles

def build_rss(all_articles, feed_title="Patch Notes Feed"):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = "http://localhost/"
    ET.SubElement(channel, "description").text = "Custom RSS feed for patch notes"

    for art in all_articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = art["title"]
        ET.SubElement(item, "link").text = art["link"]
        ET.SubElement(item, "description").text = art["description"]
        ET.SubElement(item, "pubDate").text = art["pubDate"]
        ET.SubElement(item, "guid").text = art["guid"]
        if art.get("image"):
            ET.SubElement(item, "enclosure", url=art["image"], type="image/jpeg")

    return ET.ElementTree(rss)

def main():
    all_articles = []

    with open("urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    for url in urls:
        print(f"Scraping {url} ...")
        try:
            articles = fetch_articles(url)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Failed {url}: {e}")

    if not all_articles:
        print("No articles scraped. Check selectors.")
        return

    rss_tree = build_rss(all_articles)
    rss_tree.write("feed.xml", encoding="utf-8", xml_declaration=True)
    print("Feed written to feed.xml")

if __name__ == "__main__":
    main()
