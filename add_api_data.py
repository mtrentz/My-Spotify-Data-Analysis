from decouple import config
from tqdm import tqdm
import time
import sqlite3
import requests
import datetime

def simple_log(msg):
    with open('add_api_logs.txt', 'a+') as f:
        f.write(msg)
        f.write('\n')

def execute_insert_sql(cursor, sql_str, vals):
    try:
        cursor.execute(sql_str, vals)
        return cursor.lastrowid
    except Exception as _:
        return None

def execute_fetch_all(cursor, sql_str):
    try:
        cursor.execute(sql_str)
        all = cursor.fetchall()
        return all
    except Exception as _:
        return None

  
def execute_fetch_one(cursor, sql_str, vals):
    try:
        cursor.execute(sql_str, vals)
        result = cursor.fetchone()
        if result:
          return result
        else:
          return None
    except Exception as _:
        return None

def make_request(url):
  r = requests.get(url)
  j = r.json()
  time.sleep(0.2)
  return j

def unpack_track_info(j):
  try:
    artist_mbid = j['track']['artist']['mbid']
  except KeyError:
    artist_mbid = None

  try:
    track_mbid = j['track']['mbid']
  except KeyError:
    track_mbid = None

  try:
    album_name = j['track']['album']['title']
  except KeyError:
    album_name = None

  try:
    album_mbid = j['track']['album']['mbid']
  except KeyError:
    album_mbid = None

  try:
    listeners = int(j['track']['listeners'])
  except KeyError:
    listeners = None

  try:
    playcount = j['track']['playcount']
  except KeyError:
    playcount = None

  try:
    duration = j['track']['duration']
  except KeyError:
    duration = None

  try:
    published_on = j['track']['wiki']['published']
  except KeyError:
    published_on = None

  try:
    tags = [tag['name'] for tag in j['track']['toptags']['tag']]
  except KeyError:
    tags = None

  date_updated = str(datetime.datetime.today().date())

  return track_mbid, artist_mbid, album_mbid, album_name, listeners, duration, playcount, date_updated, published_on, tags


### CONNECT TO DATABASE
conn = sqlite3.connect('music.db')
c = conn.cursor()

LAST_FM_KEY = config("LAST_FM_KEY")

### GET TRACKS (ONLY ONCE) NOT YET ADDED TO THE DATABASE (api requested)
# Tuple (artist, track)
unique_tracks_sql = """
SELECT DISTINCT 
    artist_name,
    track_name 
FROM user_data  
LEFT JOIN
    artists
    ON user_data.artist_name = artists.name
LEFT JOIN
    tracks
    ON user_data.track_name = tracks.name AND artists.mbid = tracks.artist_mbid
WHERE user_data.track_name NOT IN (SELECT name FROM tracks) AND artist_name NOT IN (SELECT name FROM artists)
"""
unique_tracks = execute_fetch_all(c, unique_tracks_sql)

for artist, song in tqdm(unique_tracks, total=len(unique_tracks)):
  ### GET TRACK INFO
  try:
    # song_to_req and artist_to_req only fixes up the texts for the request
    # This removes most of the - Remasters and - Live and stuff...
    song_to_req = song.split(' - ')[0]
    # spaces to +, just in case, to send over the url
    # TODO: Encode this properly, songs with '#' on the name are bugging out.
    song_to_req = song_to_req.replace(' ', '+')
    artist_to_req = artist.replace(' ', '+')
    song_info_url = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={LAST_FM_KEY}&artist={artist_to_req}&track={song_to_req}&autocorrect=1&format=json'
    j = make_request(song_info_url)
    # unpacks all info, some of it might actually be Nones
    track_mbid, artist_mbid, album_mbid, album_name, listeners, duration, playcount, updated_on, date_published, tags = unpack_track_info(j)
  except Exception as e:
    simple_log(f'ERROR: artist: {artist}; track: {song}')
    continue

  ### ADD TRACK INFO TO THE DATABASE

  ## Artist Info
  # if the artist was actually found
  if artist_mbid:
    artist_check_sql = "SELECT rowid FROM artists WHERE mbid=?"
    artist_vals = (artist_mbid,)
    artist_check_result = execute_fetch_one(c, artist_check_sql, artist_vals)
    # If artists wasnt yet on db
    if not artist_check_result:
      insert_artist_data_sql = "INSERT INTO artists (mbid, name) VALUES (?,?)"
      # The id comes from Last Fm (music brainz id), the artist name itself is from the spotify data. COULD not be the correct mbid
      artist_vals = (artist_mbid, artist)
      execute_insert_sql(c, insert_artist_data_sql, artist_vals)
      

  ## Tags info (like genres, but very broad)
  if tags:
    for tag in tags:
      # Check if already exists
      tag_check_sql = "SELECT rowid, tag_name FROM tags WHERE tag_name=?"
      tag_vals = (tag,)
      tag_check_result = execute_fetch_one(c, tag_check_sql, tag_vals)
      # If exists, saves its ID to use on the future
      if tag_check_result:
        tag_id = tag_check_result[0]
      # If not, adds it and gets the tag id
      else:
        insert_tag_data_sql = "INSERT INTO tags VALUES (?)"
        # tag vals ja definido
        tag_id = execute_insert_sql(c, insert_tag_data_sql, tag_vals)

      ## Track Tags (this links the tags to the track itself)
      # There is a chance that the API didnt return the tag mbid I think.
      if track_mbid:
        # Check if track id and tag are already added
        track_tag_check_sql = "SELECT track_mbid, tag_id FROM track_tags WHERE track_mbid=? AND tag_id=?"
        track_tag_vals = (track_mbid, tag_id)
        track_tag_check_result = execute_fetch_one(c, track_tag_check_sql, track_tag_vals)
        if not track_tag_check_result:
          insert_track_tag_data_sql = "INSERT INTO track_tags (track_mbid, tag_id) VALUES (?,?)"
          track_tag_vals = (track_mbid, tag_id)
          execute_insert_sql(c, insert_track_tag_data_sql, track_tag_vals)
        # Apparently, the API returns the tags ordered. So the first one in the list is kind of the "main tag/genre" of the song
        # in this case, i'll add  this into another separate table as well.
        if tag == tags[0]:
          # Same check as before
          top_track_tag_check_sql = "SELECT track_mbid, tag_id FROM top_track_tags WHERE track_mbid=? AND tag_id=?"
          top_track_tag_vals = (track_mbid, tag_id)
          top_track_tag_check_result = execute_fetch_one(c, top_track_tag_check_sql, top_track_tag_vals)
          if not top_track_tag_check_result:
            insert_top_track_tag_data_sql = "INSERT INTO top_track_tags (track_mbid, tag_id) VALUES (?,?)"
            top_track_tag_vals = (track_mbid, tag_id)
            execute_insert_sql(c, insert_top_track_tag_data_sql, top_track_tag_vals)

  ## Albums
  # Here i'm creating a table linking albuns to artists. In the future I will get the API info for all the songs in an album and fill those in
  if album_name and album_mbid and artist_mbid:
    album_check_sql = "SELECT rowid FROM albums WHERE mbid=?"
    album_vals = (album_mbid,)
    album_check_result = execute_fetch_one(c, album_check_sql, album_vals)
    if not album_check_result:
      insert_album_data_sql = "INSERT INTO albums (mbid, name, artist_mbid) VALUES (?,?,?)"
      album_vals = (album_mbid, album_name, artist_mbid)
      execute_insert_sql(c, insert_album_data_sql, album_vals)

  ## Tracks
  # Aqui só necessito que tenha track_mbid e artist_mbid. Artist_name e track_name sempre vai ter
  if track_mbid and artist_mbid:
    track_check_sql = "SELECT rowid FROM tracks WHERE mbid=?"
    track_vals = (track_mbid,)
    track_check_result = execute_fetch_one(c, track_check_sql, track_vals)
    # Se nao existe ainda a musica
    if not track_check_result:
      insert_track_data_sql = "INSERT INTO tracks (mbid, name, artist_mbid, album_mbid, listeners, duration, playcount, updated_on, date_published) VALUES (?,?,?,?,?,?,?,?,?)"
      # Eu aqui adiciono o 'mbid' do last.fm e o 'artist' que vem do spotify. Coloco o nome diretamente do spotify, se ocorre alguma correcao no last.fm eu ignoro
      track_vals = (track_mbid, song, artist_mbid, album_mbid, listeners, duration, playcount, updated_on, date_published)
      execute_insert_sql(c, insert_track_data_sql, track_vals)

conn.commit()