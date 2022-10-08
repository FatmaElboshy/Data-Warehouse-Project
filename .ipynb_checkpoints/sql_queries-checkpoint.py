import configparser


# CONFIG
config = configparser.ConfigParser()
config.read('dwh.cfg')

ARN             = config.get('IAM_ROLE', 'ARN')
LOG_DATA        = config.get('S3', 'LOG_DATA')
LOG_JSONPATH    = config.get('S3', 'LOG_JSONPATH')
SONG_DATA       = config.get('S3', 'SONG_DATA')

# DROP TABLES

staging_events_table_drop = "DROP TABLE IF EXISTS staging_events"
staging_songs_table_drop = "DROP TABLE IF EXISTS staging_songs"
songplay_table_drop = "DROP TABLE IF EXISTS songplays"
user_table_drop = "DROP TABLE IF EXISTS users"
song_table_drop = "DROP TABLE IF EXISTS songs"
artist_table_drop = "DROP TABLE IF EXISTS artists"
time_table_drop = "DROP TABLE IF EXISTS time"

# CREATE TABLES

staging_events_table_create= ("""
    CREATE TABLE IF NOT EXISTS staging_events (
                event_id            BIGINT IDENTITY(0,1),
                artist              VARCHAR,
                auth                VARCHAR,
                firstName           VARCHAR,
                gender              VARCHAR,
                itemInSession       INTEGER,
                lastName            VARCHAR,
                length              DECIMAL,
                level               VARCHAR,
                location            VARCHAR,
                method              VARCHAR,
                page                VARCHAR,
                registration        VARCHAR,
                sessionId           INTEGER     SORTKEY DISTKEY,
                song                VARCHAR,
                status              INTEGER,
                ts                  BIGINT,
                userAgent           VARCHAR,
                userId              INTEGER);
""")

staging_songs_table_create = ("""
    CREATE TABLE IF NOT EXISTS staging_songs (
                num_songs           INTEGER,
                artist_id           VARCHAR     SORTKEY DISTKEY,
                artist_latitude     VARCHAR,
                artist_longitude    VARCHAR,
                artist_location     VARCHAR,
                artist_name         VARCHAR,
                song_id             VARCHAR,
                title               VARCHAR,
                duration            DECIMAL(10),
                year                INTEGER);
""")

songplay_table_create = ("""
    CREATE TABLE IF NOT EXISTS songplays (
                songplay_id         INTEGER IDENTITY(0,1) NOT NULL  PRIMARY KEY SORTKEY,
                start_time          TIMESTAMP             NOT NULL,
                user_id             VARCHAR                                     DISTKEY,
                level               VARCHAR               NOT NULL,
                song_id             VARCHAR,
                artist_id           VARCHAR,
                session_id          VARCHAR               NOT NULL,
                location            VARCHAR,
                user_agent          VARCHAR);
""")

user_table_create = ("""
    CREATE TABLE IF NOT EXISTS users (
                user_id         INTEGER     PRIMARY KEY   SORTKEY,
                first_name      VARCHAR,
                last_name       VARCHAR,
                gender          VARCHAR,
                level           VARCHAR);
""")

song_table_create = ("""
    CREATE TABLE IF NOT EXISTS songs (
                song_id         VARCHAR     PRIMARY KEY  SORTKEY,
                title           VARCHAR,
                artist_id       VARCHAR,
                year            INTEGER,
                duration        DECIMAL(10));
""")

artist_table_create = ("""
    CREATE TABLE IF NOT EXISTS artists (
                artist_id       VARCHAR    PRIMARY KEY  SORTKEY,
                name            VARCHAR,
                location        VARCHAR,
                latitude        DECIMAL(10),
                longitude       DECIMAL(10));
""")

time_table_create = ("""
    CREATE TABLE IF NOT EXISTS time (
                start_time      TIMESTAMP  PRIMARY KEY   SORTKEY,
                hour            INTEGER,
                day             INTEGER,
                week            INTEGER,
                month           INTEGER,
                year            INTEGER,
                weekday         INTEGER);
""")

# STAGING TABLES

staging_events_copy = ("""
    COPY staging_events FROM {}
    credentials 'aws_iam_role={}'
    format as json {}
    STATUPDATE ON
    region 'us-west-2';
""").format(LOG_DATA, ARN, LOG_JSONPATH)

staging_songs_copy = ("""
    COPY staging_songs FROM {}
    credentials 'aws_iam_role={}'
    format as json 'auto'
    ACCEPTINVCHARS AS '^'
    STATUPDATE ON
    region 'us-west-2';
""").format(SONG_DATA, ARN)

# FINAL TABLES

songplay_table_insert = ("""
        INSERT INTO songplays (
               start_time, 
                user_id, 
                level, 
                song_id, 
                artist_id, 
                session_id, 
                location, 
                user_agent)
        
         SELECT
                TIMESTAMP 'epoch' + events.ts/1000 * interval '1 second' AS start_time,
                events.userId     AS user_id, 
                events.level       AS level, 
                songs.song_id      AS song_id, 
                songs.artist_id    AS artist_id, 
                events.sessionId  AS session_id, 
                events.location    AS location, 
                events.userAgent  AS user_agent
                
          FROM staging_events events
          LEFT JOIN staging_songs songs
          ON events.song = songs.title
          AND events.artist = songs.artist_name
          AND events.length = songs.duration
    """)


user_table_insert = ("""
    INSERT INTO users (                 user_id,
                                        first_name,
                                        last_name,
                                        gender,
                                        level)
                                        
    SELECT  DISTINCT userId          AS user_id,
            firstName                AS first_name,
            lastName                 AS last_name,
            gender                   AS gender,
            level                    AS level
    FROM staging_events
    WHERE page = 'NextSong';
""")

song_table_insert = ("""
    INSERT INTO songs (                 song_id,
                                        title,
                                        artist_id,
                                        year,
                                        duration)
                                        
    SELECT  DISTINCT song_id         AS song_id,
            title                    AS title,
            artist_id                AS artist_id,
            year                     AS year,
            duration                 AS duration
    FROM staging_songs;
""")

artist_table_insert = ("""
    INSERT INTO artists (               artist_id,
                                        name,
                                        location,
                                        latitude,
                                        longitude)
                                        
    SELECT  DISTINCT artist_id       AS artist_id,
            artist_name              AS name,
            artist_location          AS location,
            artist_latitude          AS latitude,
            artist_longitude         AS longitude
    FROM staging_songs;
""")

time_table_insert = ("""
    INSERT INTO time (                  start_time,
                                        hour,
                                        day,
                                        week,
                                        month,
                                        year,
                                        weekday)
                                        
    SELECT TIMESTAMP 'epoch' + ts/1000 * interval '1 second' AS start_time,
            EXTRACT(hour FROM start_time)    AS hour,
            EXTRACT(day FROM start_time)     AS day,
            EXTRACT(week FROM start_time)    AS week,
            EXTRACT(month FROM start_time)   AS month,
            EXTRACT(year FROM start_time)    AS year,
            EXTRACT(week FROM start_time)    AS weekday
    FROM    staging_events                  
    WHERE page = 'NextSong';
""")

# QUERY LISTS

create_table_queries = [staging_events_table_create, staging_songs_table_create, songplay_table_create, user_table_create, song_table_create, artist_table_create, time_table_create]
drop_table_queries = [staging_events_table_drop, staging_songs_table_drop, songplay_table_drop, user_table_drop, song_table_drop, artist_table_drop, time_table_drop]
copy_table_queries = [staging_events_copy, staging_songs_copy]
insert_table_queries = [songplay_table_insert, user_table_insert, song_table_insert, artist_table_insert, time_table_insert]
