import requests
import html
from bs4 import BeautifulSoup
from datetime import datetime
import email.utils as eut

URL = "https://www.krvs.org/podcast/interviews-from-bonjour-louisiane-on-krvs"

def fetch_episodes():
    r = requests.get(URL, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    episodes = []

    # Each episode is inside <li class="EplA-items-item">
    for li in soup.select("li.EplA-items-item"):
        
        # Title + link
        title_tag = li.select_one(".PromoAE-title a")
        if not title_tag:
            continue
        title = title_tag.get_text(strip=True)
        link = title_tag["href"]

        # Description
        desc_tag = li.select_one(".PromoAE-description")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        # Date
        date_tag = li.select_one(".PromoAE-timestamp")
        if date_tag and date_tag.get("data-date"):
            raw_date = date_tag["data-date"]
            try:
                pubdate = eut.format_datetime(datetime.strptime(raw_date, "%b %d, %Y"))
            except ValueError:
                pubdate = eut.format_datetime(datetime.utcnow())
        else:
            pubdate = eut.format_datetime(datetime.utcnow())

        # Audio URL
        audio_tag = li.select_one("ps-stream-url")
        audio_url = audio_tag.get("data-stream-url") if audio_tag else None

        if not audio_url:
            print(f"Skipping episode without audio: {title}")
            continue

        episodes.append({
            "title": title,
            "description": description,
            "audio": audio_url,
            "pubdate": pubdate,
            "guid": audio_url
        })

    return episodes


def build_rss(items):
    header = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>Interviews from Bonjour Louisiane (KRVS)</title>
    <link>https://www.krvs.org/podcast/interviews-from-bonjour-louisiane-on-krvs</link>
    <description>Interviews excerpted from KRVS’s weekday sunrise program Bonjour Louisiane.</description>
    <language>en</language>
"""

    body = ""
    for item in items:
        title = html.escape(item['title'])
        description = html.escape(item['description'])
        guid = html.escape(item['guid'])
        audio = html.escape(item['audio'])

        body += f"""
    <item>
      <title>{title}</title>
      <description>{description}</description>
      <pubDate>{item['pubdate']}</pubDate>
      <enclosure url="{audio}" length="0" type="audio/mpeg"/>
      <guid>{guid}</guid>
    </item>
"""

    footer = """
  </channel>
</rss>
"""

    return header + body + footer



def main():
    episodes = fetch_episodes()
    print(f"Found {len(episodes)} episodes.")
    rss = build_rss(episodes)

    with open("./krvs-feed/krvs-interviews.xml", "w", encoding="utf-8") as f:
        f.write(rss)


if __name__ == "__main__":
    main()
