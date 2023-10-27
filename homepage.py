import random

import psycopg2
from sshtunnel import SSHTunnelForwarder

import program_vars
import sensitive

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"

try:
    with SSHTunnelForwarder(('starbug.cs.rit.edu', 22),
                            ssh_username=username,
                            ssh_password=password,
                            remote_bind_address=('127.0.0.1', 5432)) as server:
        server.start()
        print("SSH tunnel established")
        params = {
            'database': dbName,
            'user': username,
            'password': password,
            'host': 'localhost',
            'port': server.local_bind_port
        }

        conn = psycopg2.connect(**params)
        curs = conn.cursor()
        print("Database connection established")

        try:
            print("Welcome to the homepage")

            user_id = program_vars.USER_ID

            query = "SELECT name, COUNT(playlist_has_song.songid) AS num_songs, SUM(song.duration) " \
                    "AS total_duration " \
                    "FROM playlist " \
                    "JOIN playlist_has_song ON playlist_has_song.songid = song.songid " \
                    "WHERE user_is = %s " \
                    "GROUP BY name " \
                    "ORDER BY name ASC " \


            curs.execute(query, (user_id,))

            playlist = curs.fetchall()

            for playlist in playlist:
                name, num_songs, total_duration = playlist
                print(f"Playlist Name: {name}")
                print(f"Number of Songs in Playlist: {num_songs}")
                print(f"Total Duration in Minutes: {total_duration} minutes")

            # Collections and their names if user is existing
            # must show playlist name, num songs in playlist, length of playlist

            # Top artists
            # Users following
            # Link to create playlist
        except Exception as e:  # debugging purposes
            print("user db changes failed.")
            print(e)

        conn.commit()

        conn.close()
except:
    print("Connection failed")
