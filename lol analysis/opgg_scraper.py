import sqlite3
from time import sleep

import urllib3
from bs4 import BeautifulSoup

def retrieve_champions():
    url = f"https://op.gg/lol/champions"
    http = urllib3.PoolManager()
    response = http.request('GET', url, decode_content=True)
    reply = response.data

    soup = BeautifulSoup(reply, 'html.parser')
    champions_list = soup.find("ul", {"class": "flex flex-wrap gap-x-[14px] gap-y-3 md:grid md:flex-initial md:grid-cols-6 md:gap-2"})
    return [champion.get_text() for champion in champions_list.find_all("span", {"class": "w-[46px] truncate text-xs text-gray-500"})]

def retrieve_champion_stats(champion_name, role):
    if champion_name == "Nunu & Willump": champion_name = "Nunu"
    elif champion_name == "Renata Glasc": champion_name = "Renata"
    elif champion_name == "Wukong": champion_name = "MonkeyKing"
    champion_name = champion_name.replace(' ', '').replace("'", "").replace('.', '')

    url = f"https://op.gg/lol/champions/{champion_name}/counters/{role}"
    http = urllib3.PoolManager()
    response = http.request('GET', url, decode_content=True)
    reply = response.data

    soup = BeautifulSoup(reply, 'html.parser')
    if soup.find("span", string="Sample size is not large enough."):
        return None, None

    overall_win_rate = soup.find("b", {"class": "text-[12px] tabular-nums"}).get_text()

    matchup_ul = soup.find("ul", {"class": "border-t border-t-gray-200"})
    champions = [champion.get_text() for champion in matchup_ul.find_all("span", {"class": "min-w-0 break-words py-1 text-xs font-bold text-gray-900"})]
    winrates = [winrate.get_text() for winrate in matchup_ul.find_all("div", {"class": "flex w-[72px] shrink-0 items-center justify-center"})]

    return overall_win_rate, list(zip(champions, winrates))

champions = retrieve_champions()
m = {}; overall_win_rates = {}

for champion in champions:
    sleep(1)  # To avoid overwhelming the server with requests
    champion_win_rate, matchup_data = retrieve_champion_stats(champion, "mid")
    m[champion] = {}
    if champion_win_rate:
        overall_win_rates[champion] = champion_win_rate.replace("%", "")
        for matchup in matchup_data:
            m[champion][matchup[0]] = matchup[1].replace("%", "")

conn = sqlite3.connect('winrates.db'); cursor = conn.cursor()
cursor.executescript('''
    DROP TABLE IF EXISTS champions;
    DROP TABLE IF EXISTS matchups;

    CREATE TABLE champions (
        champion_name TEXT NOT NULL PRIMARY KEY,
        winrate decimal(5,2)
    );

    CREATE TABLE matchups (
        champion1 TEXT NOT NULL,
        champion2 TEXT NOT NULL,
        matchup_winrate decimal(5,2),
        FOREIGN KEY (champion1) references champions,
        FOREIGN KEY (champion2) references champions,
        PRIMARY KEY (champion1, champion2)
    );
''')

cursor.executemany('INSERT INTO champions (champion_name, winrate) VALUES (?, ?)', [(champion, overall_win_rates[champion]) for champion in overall_win_rates])
for champion in m:
    for matchup in m[champion]:
        cursor.execute('INSERT INTO matchups (champion1, champion2, matchup_winrate) VALUES (?, ?, ?)', (champion, matchup, m[champion][matchup]))
conn.commit()
