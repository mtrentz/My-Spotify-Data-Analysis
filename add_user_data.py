from decouple import config
from tqdm import tqdm
import pandas as pd
import sqlite3
import glob
import os
import sys

def execute_insert_sql(cursor, sql_str, vals):
    try:
        cursor.execute(sql_str, vals)
        return cursor.lastrowid
    except Exception as _:
        return None


HERE = os.path.dirname(sys.argv[0])
DATA_PATH = os.path.join(HERE, 'user_data')
LAST_FM_KEY = config("LAST_FM_KEY")

### CONNECT TO DATABASE
conn = sqlite3.connect('music.db')
c = conn.cursor()

### READ USER DATA
dfs = []

files = glob.glob(os.path.join(DATA_PATH, '*.json'))
for f in files:
    partial_df = pd.read_json(f)
    dfs.append(partial_df.copy())

df = pd.concat(dfs, ignore_index=True)
# Remove duplicated lines
df = df.loc[~df.duplicated()]
# Date to datetime
df.loc[:,'endTime'] = pd.to_datetime(df['endTime'])

### ADD DATA INTO USER_DATA
for index, row in tqdm(df.iterrows(), total=df.shape[0]):
    # Pega o dado do df
    end_time = row['endTime'].strftime('%Y-%m-%d %H:%M:%S')
    artist_name = row['artistName']
    track_name = row['trackName']
    ms_played = row['msPlayed']
    # cria o sql insert stamtement
    insert_spotify_data_sql = "INSERT OR IGNORE INTO user_data (end_time, artist_name, track_name, ms_played) VALUES (?,?,?,?)"
    vals = (end_time, artist_name, track_name, ms_played)
    execute_insert_sql(c, insert_spotify_data_sql, vals)

conn.commit()

