import sqlite3

conn = sqlite3.connect('anime_database.db')
cursor = conn.cursor()

recommendations = {}

if True:
    cursor.execute("SELECT id, num_recommendations FROM recommendations")
    for row in cursor.fetchall():
        anime_id, num_recommendations = row
        recommendations[anime_id] = num_recommendations

if True:
    watched = cursor.execute("SELECT id FROM watched").fetchall()
    recommendations = {anime_id: num_recommendations for anime_id, num_recommendations in recommendations.items() if (anime_id,) not in watched}
    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    print("Recommended anime: ")
    for anime_id, num_recommendations in sorted_recommendations:
        cursor.execute("SELECT title FROM list WHERE id = ?", (anime_id,))
        title_row = cursor.fetchone()
        title = title_row[0] if title_row else "Unknown Title"
        print(f"{title} (ID: {anime_id}) - {num_recommendations} recommendations")