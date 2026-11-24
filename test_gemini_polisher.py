import json
import urllib.request
import re

def polish_segments_with_gemini(raw_segments_text: list, proxy_url="http://127.0.0.1:8081/v1/chat/completions"):
    """
    Calls Gemini 2.5 Pro via B1 Proxy to clean and reconstruct spoken Hindi/Sanskrit/English phrases.
    """
    if not raw_segments_text:
        return raw_segments_text

    combined_input = "\n".join([f"[{i}] {t}" for i, t in enumerate(raw_segments_text)])
    prompt = f"""You are an expert audio transcriptionist specializing in Hindi, Sanskrit mantras, and Indian spiritual discourses.
Fix phonetically misheard or garbled words in these transcribed audio segments.
Keep the meaning authentic and spiritual. Clean up any broken syllables into proper Devanagari Hindi or clean English words.

Segments:
{combined_input}

Respond ONLY with JSON mapping segment index to cleaned text:
{{
  "cleaned_segments": [
     {{"index": 0, "text": "cleaned text..."}}
  ]
}}"""

    payload = json.dumps({
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "system", "content": "You are a master Hindi/Sanskrit transcription corrector. Respond in valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }).encode("utf-8")

    req = urllib.request.Request(
        proxy_url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            # parse json
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            cleaned_map = {item["index"]: item["text"] for item in parsed.get("cleaned_segments", [])}
            return [cleaned_map.get(i, raw_segments_text[i]) for i in range(len(raw_segments_text))]
    except Exception as e:
        print("Gemini polish fallback:", e)
        return raw_segments_text

test_input = ["स्विर में आपको, कारिया, विवा, संतान, अचिचा, जिदने अपना है?"]
cleaned = polish_segments_with_gemini(test_input)
print("ORIGINAL:", test_input)
print("CLEANED :", cleaned)
