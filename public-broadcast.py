import json
import requests
import os
from datetime import datetime

# === Global Setup ===
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

# === YUPPTV SECTION ===
def format_url(url):
    if not url:
        return ""
    cdn_base = "https://d229kpbsb5jevy.cloudfront.net/yuppfast/content/"
    return url if url.startswith('http') else cdn_base + url.replace(',', '/')

def format_slug(slug):
    return slug.split('/')[0]

def get_yupp_headers():
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

def fetch_yupp_channels(genre):
    url = f"https://yuppfast-api.revlet.net/service/api/v1/tvguide/channels?filter=genreCode:{genre};langCode:ENG,HIN,MAR,BEN,TEL,KAN,GUA,PUN,BHO,URD,ASS,TAM,MAL,ORI,NEP"
    return requests.get(url, headers=get_yupp_headers()).json()["response"]["data"]

def process_yupp():
    global channel_counter
    genres = ["news", "entertainment", "music", "kids", "spiritual", "movies", "lifestyle", "sports", "educational", "others"]
    for index, genre in enumerate(genres, 1):
        category = {
            "category_id": 100 + index,
            "category_name": genre.title(),
            "category_slug": genre,
            "category_description": f"{genre.title()} Category",
            "category_priority": index,
            "channels": []
        }
        try:
            for ch in fetch_yupp_channels(genre):
                slug = ch["target"].get("path", ch["target"].get("slug", ""))
                channel = {
                    "channel_id": ch["id"],
                    "channel_number": str(channel_counter).zfill(3),
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
                channel_counter += 1
            combined_json["feeds"].append(category)
        except Exception as e:
            print(f"❌ Failed to fetch YuppTV {genre}: {e}")

# === WAVES SECTION ===
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
            channels = []
            for ch in res.json().get("data", []):
                channel = {
                    "channel_id": ch["id"],
                    "channel_number": str(channel_counter).zfill(3),
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
                    "#EXTVLCOPT:http-user-agent=Dalvik/2.1.0 (Linux; Android 12; RMX3261 Build/ace2873.0)",
                    f'https://in1.sunilprasad.com.np/wavespb/{channel["channel_id"]}/master.m3u8',
                    ""
                ])
                channel_counter += 1
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

# === NEPALESE SECTION ===
def process_nepalese():
    global channel_counter
    NEPAL_API_URL = "https://ntv.newitventure.com/api/v1/ntv/channels"
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": "Bearer",
        "pragma": "no-cache",
        "cache-control": "no-cache",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "referer": "https://live.ntv.org.np/"
    }

    try:
        res = requests.get(NEPAL_API_URL, headers=headers)
        res.raise_for_status()
        items = res.json()["items"]
    except Exception as e:
        print(f"❌ Failed to fetch Nepalese channels: {e}")
        items = []

    category = {
        "category_id": 200,
        "category_name": "Nepalese",
        "category_slug": "nepalese",
        "category_description": "FTA Nepalese Channels",
        "category_priority": 1,
        "channels": []
    }

    for ch in items:
        slug = ch["slug"]
        channel = {
            "channel_id": ch["id"],
            "channel_number": str(channel_counter).zfill(3),
            "channel_country": "NP",
            "channel_category": "Nepalese",
            "channel_name": ch["title"].strip(),
            "channel_slug": slug,
            "channel_logo": ch["logo"].replace("\\/", "/"),
            "channel_poster": ch["background_logo"].replace("\\/", "/")
        }
        category["channels"].append(channel)
        m3u_lines.extend([
            f'#EXTINF:-1 tvg-id="{channel["channel_id"]}" tvg-chno="{channel["channel_number"]}" '
            f'tvg-name="{channel["channel_slug"]}" tvg-logo="{channel["channel_logo"]}" '
            f'group-title="Nepalese", {channel["channel_name"]}',
            "#KODIPROP:inputstream=inputstream.adaptive",
            "#KODIPROP:inputstream.adaptive.manifest_type=hls",
            "#EXTVLCOPT:http-user-agent=Dalvik/2.1.0 (Linux; Android 10; SM-M115F Build/QP1A.190711.020)",
            f'https://in1.sunilprasad.com.np/ntvLive/{slug}/master.m3u8',
            ""
        ])
        channel_counter += 1

    # Add Kantipur SD manually
    channel = {
        "channel_id": 999,
        "channel_number": str(channel_counter).zfill(3),
        "channel_country": "NP",
        "channel_category": "Nepalese",
        "channel_name": "Kantipur SD",
        "channel_slug": "kantipur",
        "channel_logo": "https://play-lh.googleusercontent.com/CQSmPpi6-l-S44IER_44ytPqQ-V4CbCPWspMJGNp3rYcD6VIEdiBenpMBB0DAi2Vow",
        "channel_poster": "https://play-lh.googleusercontent.com/CQSmPpi6-l-S44IER_44ytPqQ-V4CbCPWspMJGNp3rYcD6VIEdiBenpMBB0DAi2Vow"
    }
    category["channels"].append(channel)
    m3u_lines.extend([
        f'#EXTINF:-1 tvg-id="{channel["channel_id"]}" tvg-chno="{channel["channel_number"]}" '
        f'tvg-name="{channel["channel_slug"]}" tvg-logo="{channel["channel_logo"]}" '
        f'group-title="Nepalese", {channel["channel_name"]}',
        "#KODIPROP:inputstream=inputstream.adaptive",
        "#KODIPROP:inputstream.adaptive.manifest_type=hls",
        "#EXTVLCOPT:http-user-agent=Dalvik/2.1.0 (Linux; Android 10; SM-M115F Build/QP1A.190711.020)",
        "https://in1.sunilprasad.com.np/ktvLive/kantipur/master.m3u8",
        ""
    ])
    channel_counter += 1
    combined_json["feeds"].append(category)

# === MAIN ===
if __name__ == "__main__":
    for file in ["fta-data.json", "playlist.m3u8"]:
        if os.path.exists(file):
            os.remove(file)

    process_yupp()
    process_waves()
    process_nepalese()

    with open("fta-data.json", "w", encoding="utf-8") as f:
        json.dump(combined_json, f, indent=2, ensure_ascii=False)

    with open("playlist.m3u8", "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"✅ Combined playlist and JSON generated with {channel_counter - 1} channels.")
