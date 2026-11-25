import bisect; import sqlite3; import numpy as np; from scipy.special import logit

conn = sqlite3.connect('winrates.db'); cursor = conn.cursor()

x = cursor.execute('SELECT * FROM champions')

y = x.fetchall()
champion_indices = {k: v for v, k in enumerate(list(map(lambda x: x[0], sorted(y))))}

cursor.execute('SELECT * FROM matchups')

m_1 = {}; m_2 = {}; champion_winrates = {}
for (champion1, champion2, winrate) in x:
    if champion1 not in m_1:
        m_1[champion1] = [np.nan] * len(champion_indices)
    m_1[champion1][champion_indices[champion2]] = winrate / 100

for champion, winrates in m_1.items():
    champion_winrates[champion] = np.nanmean(winrates)

for champion, winrates in m_1.items():
    m_2[champion] = logit(m_1[champion]) - logit(champion_winrates[champion])

champion1 = "Viktor"; spread_1 = m_2[champion1]
m_scores = {}

for champion2, spread_2 in m_2.items():
    if champion1 == champion2: continue

    combined_spread = np.fmax(spread_1, spread_2)
    m_scores[champion2] = np.nanmean(combined_spread)

scores = sorted([(score, champion) for champion, score in m_scores.items()], reverse=True)

for entry in scores:
    print(f"{entry[1]}: {entry[0]}")