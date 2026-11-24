import urllib.request
import json
from pathlib import Path

headers = {'User-Agent': 'CineForgeAI/1.0 (isens@example.com)'}

def search_wikimedia_videos(query: str, max_results: int = 3):
    """Searches Wikimedia Commons for royalty-free public domain MP4 videos."""
    url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srsearch={urllib.parse.quote(query)}+filetype:video&srnamespace=6&srlimit={max_results}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = []
            for item in data.get('query', {}).get('search', []):
                title = item.get('title')
                # Get file info
                info_url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url|mime|size&titles={urllib.parse.quote(title)}"
                info_req = urllib.request.Request(info_url, headers=headers)
                with urllib.request.urlopen(info_req, timeout=10) as info_resp:
                    info_data = json.loads(info_resp.read().decode('utf-8'))
                    pages = info_data.get('query', {}).get('pages', {})
                    for pid, pdata in pages.items():
                        imageinfo = pdata.get('imageinfo', [])
                        if imageinfo:
                            file_url = imageinfo[0].get('url')
                            mime = imageinfo[0].get('mime')
                            results.append({"title": title, "url": file_url, "mime": mime})
            return results
    except Exception as e:
        print("Wikimedia error:", e)
        return []

print("Searching Wikimedia for 'sunrise timelapse'...")
vids = search_wikimedia_videos("sunrise timelapse", 2)
print("Found:", vids)
