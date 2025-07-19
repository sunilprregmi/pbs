import json
import requests
import os
from datetime import datetime
from typing import Dict, List

### ----- COMMON SETUP -----
now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
combined_json = {
    "date": now_str,
    "feeds": []
}
m3u_lines = [
    "#EXTM3U",
    "# Only Free-To-Air Streams",
    "# Scrapped by @sunilprregmi",
    f"# Scrapped on {now_str}",
    "# Relay server is for playback",
    ""
]
channel_counter = 1


### ----- YUPPTV SECTION -----
def format_url(url):
    if not url:
        return ""
    cdn_base = "https://d229kpbsb5jevy.cloudfront.net/yuppfast/content/"
    if url.startswith('http'):
        return url
    path = url.replace(',', '/')
    return cdn_base + path

def format_slug(slug):
    return slug.split('/')[0]

def get_yupp_headers() -> Dict:
    return {
        "sec-ch-ua-platform": "Windows",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
        "box-id": "7c03c72952b44aa4",
        "sec-ch-ua-mobile": "?0",
        "session-id": "YT-f86ef4ba-57ab-4c06-8552-245abc2c6541",
        "tenant-code": "yuppfast",
        "origin": "https://www.yupptv.com",
        "referer": "https://www.yupptv.com/",
        "accept-language": "en-US,en;q=0.9"
    }

def fetch_yupp_channels(genre: str) -> List:
    base_url = "https://yuppfast-api.revlet.net/service/api/v1/tvguide/channels"
    params = f"filter=genreCode:{genre};langCode:ENG,HIN,MAR,BEN,TEL,KAN,GUA,PUN,BHO,URD,ASS,TAM,MAL,ORI,NEP"
    url = f"{base_url}?{params}"
    response = requests.get(url, headers=get_yupp_headers())
    return response.json()["response"]["data"]

def process_yupp():
    global channel_counter
    genres = ["news", "entertainment", "music", "kids", "spiritual", "movies", "lifestyle", "sports", "educational", "others"]

    for index, genre in enumerate(genres, 1):
        category = {
            "category_id": 0 + index,
            "category_name": genre.title(),
            "category_slug": genre,
            "category_description": f"{genre.title()} Category",
            "category_priority": index,
            "channels": []
        }

        try:
            channels_data = fetch_yupp_channels(genre)
            for ch in channels_data:
                slug = ch["target"].get("path", ch["target"].get("slug", ""))
                channel_number = str(channel_counter).zfill(3)
                channel_counter += 1

                channel = {
                    "channel_id": ch["id"],
                    "channel_number": channel_number,
                    "channel_country": "IN",
                    "channel_category": genre.title(),
                    "channel_name": ch["display"]["title"],
                    "channel_slug": format_slug(slug),
                    "channel_logo": format_url(ch["display"]["imageUrl"]),
                    "channel_poster": format_url(ch["display"]["loadingImageUrl"])
                }
                category["channels"].append(channel)

                m3u_lines.extend([
                    f'#EXTINF:-1 tvg-id="{channel["channel_id"]}" tvg-chno="{channel["channel_number"]}" '
                    f'tvg-name="{channel["channel_slug"]}" tvg-logo="{channel["channel_logo"]}" '
                    f'group-title="{genre.title()}", {channel["channel_name"]}',
                    "#KODIPROP:inputstream=inputstream.adaptive",
                    "#KODIPROP:inputstream.adaptive.manifest_type=hls",
                    "#EXTVLCOPT:http-user-agent=YuppTV/7.18.1 (Linux;Android 16) ExoPlayerLib/2.19.1",
                    f'https://in1.sunilprasad.com.np/yuppLive/{channel["channel_slug"]}/master.m3u8',
                    ""
                ])
        except Exception as e:
            print(f"❌ Failed to fetch YuppTV {genre}: {e}")
        combined_json["feeds"].append(category)


### ----- WAVES SECTION -----
def process_waves():
    global channel_counter
    headers = {
        "User-Agent": "okhttp/4.12.0",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "Accept-Encoding": "gzip",
        "devicetype": "4",
        "devicemodel": "Realme RMX3261",
        "country": "Nepal",
        "age": "100",
        "deviceid": "020000000000",
        "version": "139",
        "iskid": "0",
        "langid": "1",
        "langcode": "1",
        "istempuser": "false",
        "isdefault": "0"
    }

    categories = [
        {"id": 1, "name": "News", "slug": "news", "description": "News Category", "priority": 1, "url": "https://api.wavespb.com/api/V1/getLiveChannelsV2/0/0/70"},
        {"id": 2, "name": "Entertainment", "slug": "entertainment", "description": "Entertainment Category", "priority": 2, "url": "https://api.wavespb.com/api/V1/getLiveChannelsV2/0/0/71"},
        {"id": 3, "name": "Music", "slug": "music", "description": "Music Category", "priority": 3, "url": "https://api.wavespb.com/api/V1/getLiveChannelsV2/0/0/73"},
        {"id": 5, "name": "Spiritual", "slug": "spiritual", "description": "Spiritual Category", "priority": 5, "url": "https://api.wavespb.com/api/V1/getLiveChannelsV2/0/0/72"},
        {"id": 11, "name": "DD National", "slug": "dd-national", "description": "Doordarshan National Channels", "priority": 11, "url": "https://api.wavespb.com/api/V1/getLiveChannelsV2/0/0/76"},
        {"id": 12, "name": "DD Regional", "slug": "dd-regional", "description": "Doordarshan Regional Channels", "priority": 12, "url": "https://api.wavespb.com/api/V1/getLiveChannelsV2/0/0/77"},
    ]

    for cat in categories:
        try:
            res = requests.get(cat["url"], headers=headers)
            res.raise_for_status()
            channels_raw = res.json().get("data", [])
            channels = []

            for ch in channels_raw:
                channel_number = str(channel_counter).zfill(3)
                channel_counter += 1

                channel = {
                    "channel_id": ch["id"],
                    "channel_number": channel_number,
                    "channel_country": "IN",
                    "channel_category": cat["name"],
                    "channel_name": ch["title"],
                    "channel_slug": ch["title"].lower().replace(" ", "-"),
                    "channel_logo": ch["thumbnail"],
                    "channel_poster": ch["poster_url"]
                }
                channels.append(channel)

                m3u_lines.extend([
                    f'#EXTINF:-1 tvg-id="{channel["channel_id"]}" tvg-chno="{channel["channel_number"]}" '
                    f'tvg-name="{channel["channel_slug"]}" tvg-logo="{channel["channel_logo"]}" '
                    f'group-title="{cat["name"]}", {channel["channel_name"]}',
                    "#KODIPROP:inputstream=inputstream.adaptive",
                    "#KODIPROP:inputstream.adaptive.manifest_type=hls",
                    "#EXTVLCOPT:http-user-agent=Dalvik/2.1.0 (Linux; U; Android 12; RMX3261 Build/ace2873.0)",
                    f'https://in1.sunilprasad.com.np/wavespb/{channel["channel_id"]}/master.m3u8',
                    ""
                ])

            combined_json["feeds"].append({
                "category_id": cat["id"],
                "category_name": cat["name"],
                "category_slug": cat["slug"],
                "category_description": cat["description"],
                "category_priority": cat["priority"],
                "channels": channels
            })

        except Exception as e:
            print(f"❌ Failed to fetch {cat['name']}: {e}")


### ----- MAIN COMBINER -----
if __name__ == "__main__":
    if os.path.exists("fta-data.json"):
        os.remove("fta-data.json")
    if os.path.exists("playlist.m3u8"):
        os.remove("playlist.m3u8")

    process_yupp()
    process_waves()

    with open("fta-data.json", "w", encoding="utf-8") as f:
        json.dump(combined_json, f, indent=2, ensure_ascii=False)

    with open("playlist.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"✅ Playlist and JSON generated with {channel_counter - 1} channels.")
