from datetime import datetime
import spotipy
from dotenv import load_dotenv
import os
import requests
from spotipy.oauth2 import SpotifyOAuth
import requests
from bs4 import BeautifulSoup
import re

#___________________________________LOAD SPOTIFY CREDENTIALS FROM DOTENV____________________________________#

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")


#______________________FUNCTION TO VALIDATE AND CONSTRUCT THE BILLBOARD URL_______________________#

def get_endpoint(date):
    """validates and returns the Billboard top 100 for a given date"""

    while True:
        try:
            datetime.strptime(date, "%Y-%m-%d")
            break
        except ValueError:
            print("Sorry! Your input does not match the format YYYY-MM-DD. Please try again")
            date = input("Which year do you want to travel to? Type date in this format YYYY-MM-DD: ")
    return f"https://www.billboard.com/charts/hot-100/{date}/"


#_______________________GET THE USER INPUT AND FETCH THE BILLBOARD CHART______________________________#
user_input = input("Which year do you want to travel to? Type date in this format YYYY-MM-DD: ")
endpoint = get_endpoint(user_input)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

response = requests.get(url=endpoint, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

#_______________________________EXTRACT SONGS AND ARTISTS_________________________________#

songs = soup.select("div ul li ul li h3")
artists = soup.select("span.c-label.a-no-trucate")

song_titles = [song.getText(strip=True) for song in songs]
song_artists = [artist.getText(strip=True) for artist in artists]
top_100 = list(zip(song_titles, song_artists))
#print(top_100)

#______________________AUTHENTICATE WITH SPOTIFY API______________________________#
sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        scope="playlist-modify-public",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI
    )
)
user = sp.current_user()
user_id = user["id"]
print(f" Authenticated as {user_id}")


#_________________________ SEARCH FOR THE SONGS ON SPOTIFY USING THE SONG URI_____________________________#

def clean_artist_name(artist):
    """
    Extracts the main artist name by removing 'featuring', 'feat.', 'ft.', 'x', and '&'.
    """
    return re.split(r"\s+(featuring|feat\.|ft\.|x|&)\s+", artist, flags=re.IGNORECASE)[0]


spotify_uris = []
formatted_songs = [(song, clean_artist_name(artist)) for song, artist in top_100]
print(formatted_songs)

for artist, song in formatted_songs:
    result = sp.search(q=f"{song} {artist}", type="track", limit=1)
    tracks = result.get("tracks", []).get("items", [])

    if tracks:
        spotify_uris.append(tracks[0]["uri"])
    else:
        print(f"song '{song}' by '{artist}' not found")

print(spotify_uris)

#_______________________________CREATE NEW PLAYLIST AND ADD SONGS_______________________________#

playlist_name = f"Billboard top 100 as at {user_input} "
playlist_description = f"Top 100 songs from Billboard on {user_input}"
playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True, description=playlist_description)

if spotify_uris:
    sp.playlist_add_items(playlist_id=playlist["id"], items=spotify_uris)
    print(f"Successfully added {len(spotify_uris)} songs to the playlist: {playlist_name}")

else:
    print("no valid songs to add to the playlist")
