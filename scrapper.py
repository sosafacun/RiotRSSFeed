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

    # Riot pages mark patch cards with this attribute
    cards = soup.select("a[data-testid='articlefeaturedcard-component']")

    for card in cards:
        title_el = card.select_one("[data-testid='card-title']")
        desc_el = card.select_one("[data-testid='card-description']")
        time_el = card.select_one("time")

        title = title_el.get_text(strip=True) if title_el else "Sin título"
        desc = desc_el.get_text(strip=True) if desc_el else ""
        href = card.get("href", "")
        if href.startswith("/"):
            href = url.split("/")[0] + "//" + url.split("/")[2] + href
        pub_date = (
            datetime.strptime(time_el["datetime"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%a, %d %b %Y %H:%M:%S GMT")
            if time_el and time_el.has_attr("datetime")
            else datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        )
        guid = hashlib.md5(href.encode("utf-8")).hexdigest()

        articles.append({
            "title": title,
            "link": href,
            "description": desc,
            "pubDate": pub_date,
            "guid": guid
        })

    return articles

def build_rss(all_articles, feed_title="Sale con fritas NEWS"):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = feed_title
    ET.SubElement(channel, "link").text = "http://localhost/"
    ET.SubElement(channel, "description").text = "El RSS que querés para todas tus noticias"

    for art in all_articles:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = art["title"]
        ET.SubElement(item, "link").text = art["link"]
        ET.SubElement(item, "description").text = art["description"]
        ET.SubElement(item, "pubDate").text = art["pubDate"]
        ET.SubElement(item, "guid").text = art["guid"]

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
