import sqlite3

### CREATES DATABASE
conn = sqlite3.connect('music.db')
c = conn.cursor()

user_data_table = """
CREATE TABLE IF NOT EXISTS user_data(
    end_time DATETIME,
    artist_name VARCHAR(255),
    track_name VARCHAR(255),
    ms_played INTEGER,
    UNIQUE(end_Time, artist_name, track_name, ms_played)
);
"""
c.execute(user_data_table)

artists_table = """
CREATE TABLE IF NOT EXISTS artists
  (
  mbid VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL
  )
"""
c.execute(artists_table)

album_table = """
CREATE TABLE IF NOT EXISTS albums(
    mbid VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    artist_mbid VARCHAR(255) NOT NULL,
    FOREIGN KEY(artist_mbid)
      REFERENCES artists(mbid)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""
c.execute(album_table)

tracks_table = """
CREATE TABLE IF NOT EXISTS tracks(
    mbid VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    artist_mbid VARCHAR(255) NOT NULL,
    album_mbid VARCHAR(255) NULL,
    listeners INTEGER NULL,
    duration INTEGER NULL,
    playcount INTEGER NULL,
    updated_on DATE NULL,
    date_published VARCHAR(255) NULL,
    FOREIGN KEY(artist_mbid)
      REFERENCES artists(mbid)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(album_mbid)
      REFERENCES albums(mbid)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""
c.execute(tracks_table)

tags_table = """
CREATE TABLE IF NOT EXISTS tags(
    tag_name VARCHAR(255) UNIQUE
    );
"""
c.execute(tags_table)

# Only track top tag
top_track_tags_table = """
CREATE TABLE IF NOT EXISTS top_track_tags(
    track_mbid VARCHAR(255) UNIQUE,
    tag_id INTEGER,
    PRIMARY KEY (track_mbid, tag_id),
    FOREIGN KEY(track_mbid)
      REFERENCES tracks(mbid)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(tag_id)
      REFERENCES tags(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""
c.execute(top_track_tags_table)

track_tags_sql = """
CREATE TABLE IF NOT EXISTS track_tags(
    track_mbid VARCHAR(255),
    tag_id INTEGER,
    PRIMARY KEY (track_mbid, tag_id),
    FOREIGN KEY(track_mbid)
      REFERENCES tracks(mbid)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY(tag_id)
      REFERENCES tags(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);
"""
c.execute(track_tags_sql)

conn.commit()