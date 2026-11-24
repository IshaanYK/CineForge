import urllib.request
import re
import json

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

print("Testing Mixkit...")
try:
    url = "https://mixkit.co/free-stock-video/nature/"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        mp4s = re.findall(r'https://assets\.mixkit\.co/videos/preview/[^"\']+\.mp4', html)
        print("Mixkit found MP4s:", len(mp4s))
        if mp4s:
            print("Sample Mixkit MP4:", mp4s[0])
except Exception as e:
    print("Mixkit error:", e)

print("\nTesting Pexels...")
try:
    url = "https://www.pexels.com/search/videos/meditation/"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        # Pexels embeds video URLs or data
        vids = re.findall(r'https://images\.pexels\.com/videos/[^"\']+\.mp4', html)
        print("Pexels found MP4s:", len(vids))
        if vids:
            print("Sample Pexels MP4:", vids[0])
except Exception as e:
    print("Pexels error:", e)

print("\nTesting Pixabay...")
try:
    # Pixabay direct search
    url = "https://pixabay.com/videos/search/nature/"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        vids = re.findall(r'https://cdn\.pixabay\.com/video/[^"\']+\.mp4', html)
        print("Pixabay found MP4s:", len(vids))
        if vids:
            print("Sample Pixabay MP4:", vids[0])
except Exception as e:
    print("Pixabay error:", e)
