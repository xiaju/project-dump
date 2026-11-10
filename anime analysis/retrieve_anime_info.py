from pprint import pprint
import sqlite3
import time
from urllib import response
import requests
import os

username = os.environ["USERNAME"]; client_id = os.environ["CLIENT_ID"]
conn = sqlite3.connect('anime_database.db'); cursor = conn.cursor()

cursor.executescript('''
    DROP TABLE IF EXISTS watched;
    DROP TABLE IF EXISTS list;
    DROP TABLE IF EXISTS recommendations;
    DROP TABLE IF EXISTS genres;

    CREATE TABLE list (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        photo_url TEXT NOT NULL,
        synopsis TEXT NOT NULL
    );

    CREATE TABLE watched (
        id INTEGER PRIMARY KEY REFERENCES list(id)
    );

    CREATE TABLE recommendations (
        num_recommendations INTEGER NOT NULL,
        id Integer PRIMARY KEY REFERENCES list(id)
    );

    CREATE TABLE genres (
        id INTEGER REFERENCES LIST(id),
        genre TEXT NOT NULL,
        PRIMARY KEY (id, genre)
    );
''')

headers = { "X-MAL-CLIENT-ID": client_id }
watched = set()
recommendation_counts = {}

def execute_with_retry(url, params, headers, max_attempts=3):
    for attempt in range(max_attempts):
        if attempt > 0:
            time.sleep(2 ** (attempt - 1))
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 504 and response.status_code != 204:
            break

    if response.status_code == 504:
        print(f"Failed to retrieve data from {url} after {max_attempts} attempts. Status code: {response.status_code}")
        exit(1)
    elif response.status_code != 200:
        print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")
        exit(1)
    return response

if True:
    params = { "status": "completed", "nsfw": "true" }
    extend_watched = lambda response: watched.update(set(map(lambda anime: anime["node"]["id"], response.json()["data"])))

    response = requests.get(f"https://api.myanimelist.net/v2/users/{username}/animelist", headers=headers, params=params)
    extend_watched(response)

    while response.json().get("paging", {}).get("next"):
        url = response.json()["paging"]["next"]
        response = requests.get(url, headers=headers)
        extend_watched(response)

cursor.executemany("INSERT INTO watched (id) VALUES (?)", [(anime_id,) for anime_id in watched])

if True:
    params = { "fields": "recommendations" }
    for anime_id in watched:
        response = execute_with_retry(f"https://api.myanimelist.net/v2/anime/{anime_id}", params=params, headers=headers)
        data = response.json();

        for recommendation in data.get("recommendations", {}):
            rec_id = recommendation["node"]["id"]; rec_count = recommendation["num_recommendations"]
            recommendation_counts[rec_id] = recommendation_counts.get(rec_id, 0) + rec_count

    cursor.executemany("INSERT INTO recommendations (num_recommendations, id) VALUES (?, ?)", [(rec_count, rec_id) for rec_id, rec_count in recommendation_counts.items()]) 

if True:
    for anime_id in watched | recommendation_counts.keys():
        params = { "fields": "id,title,main_picture,synopsis,genres" }
        response = execute_with_retry(f"https://api.myanimelist.net/v2/anime/{anime_id}", params=params, headers=headers)
        data = response.json()

        cursor.execute("INSERT INTO list (id, title, photo_url, synopsis) VALUES (?, ?, ?, ?)", (data["id"], data["title"], data["main_picture"]["medium"], data["synopsis"]))
        cursor.executemany("INSERT INTO genres (id, genre) VALUES (?, ?)", [(data["id"], genre) for genre in [genre["name"] for genre in data.get("genres", [])]])

conn.commit(); conn.close()