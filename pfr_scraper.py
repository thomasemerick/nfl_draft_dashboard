import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

ol_positions = ["T", "G", "C", "OT", "OG", "OL"]

def get_game_urls(year):
    url = f"https://www.pro-football-reference.com/years/{year}/week_1.htm"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        if "/boxscores/" in a["href"] and a["href"].endswith(".htm"):
            full = "https://www.pro-football-reference.com" + a["href"]
            if full not in links:
                links.append(full)
    return links

def get_starters(game_url):
    time.sleep(4)  # polite delay
    r = requests.get(game_url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for side in ["vis_starters", "home_starters"]:
        table = soup.find("table", {"id": side})
        if not table:
            continue
        for row in table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            player = cols[0].get_text(strip=True)
            pos = cols[1].get_text(strip=True)
            if pos in ol_positions:
                results.append({"player": player, "pos": pos})
    return results

all_starters = []
for year in range(2020, 2026):
    print(f"\nScraping {year}...")
    game_urls = get_game_urls(year)
    print(f"  Found {len(game_urls)} games")
    for game_url in game_urls:
        # Extract teams from URL
        match = re.search(r'/boxscores/(\d+)(\w+)\.htm', game_url)
        if not match:
            continue
        starters = get_starters(game_url)
        for s in starters:
            s["season"] = year
            s["game_url"] = game_url
        all_starters.extend(starters)
        print(f"  {game_url}: {len(starters)} OL starters")

df = pd.DataFrame(all_starters)
df.to_csv("pfr_week1_starters.csv", index=False)
print(f"\nSaved {len(df)} rows to pfr_week1_starters.csv")