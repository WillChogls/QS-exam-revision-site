"""Download past-paper metadata from SQA's past paper finder into data/sqa_papers.json.

Run: python scrape_sqa.py   (about 190 requests, ~2 minutes)

Only metadata (subject, level, year, title, URL) is saved; no PDFs are downloaded.
seed.py reads the JSON, so seeding never touches the network.
"""
import json
import os
import re
import time
import urllib.parse
import urllib.request

FINDER = "https://www.sqa.org.uk/pastpapers/findpastpaper.htm"
LEVELS = {"N5": "n5", "NH": "higher", "NAH": "ah"}
KEEP = ("subject", "paper", "year", "type", "fileType", "url")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sqa_papers.json")


def get(params=None):
    url = FINDER + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={"User-Agent": "personal-revision-site/1.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode()


def js_array(html, name):
    start = html.index(f"var {name} = ") + len(f"var {name} = ")
    return json.JSONDecoder().raw_decode(html, start)[0]


def main():
    subjects = re.findall(r'<option value="([^"]+)"', get().split('id="level"')[0])
    records = []
    for subject in subjects:
        for sqa_level, level in LEVELS.items():
            html = get({"subject": subject, "level": sqa_level})
            for r in js_array(html, "papersAr") + js_array(html, "misAr"):
                records.append({"level": level, **{k: r[k] for k in KEEP}})
            time.sleep(0.3)  # be polite to sqa.org.uk
        print(f"{subject}: {sum(r['subject'] == subject for r in records)} files")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(records, f, indent=1, ensure_ascii=False)
    print(f"Saved {len(records)} records from {len(subjects)} subjects to {OUT}")


if __name__ == "__main__":
    main()
