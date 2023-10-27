import random

import psycopg2
from sshtunnel import SSHTunnelForwarder

import sensitive
import program_vars

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

            user_id = program_vars.USER_ID  # replace with actuasl user ID
            curs.execute("SELECT userid FROM listeners_listensto_playlist"
                         "where userid = %s", (user_id,))
            #if user_id in listeners_listento_playlist:

            curs.execute("SELECT playlist_name FROM playlists "
                         "WHERE userid = %s "
                         "ORDER BY playlist_name ASC", (user_id,))
            playlists = curs.fetchall()

            if playlists:
                print("This is a list of all your playlists by name in ascending order:")
                for playlist in playlists:
                    print(playlist[0])
            else:
                print("You haven't created any playlists yet.")

            playlist_id = 1  # replace with actual playlist ID

            curs.execute("SELECT quantity, "
                         "length FROM PLAYLIST WHERE playlist_id = %s", (playlist_id,))

            result = curs.fetchone(0)

            # get user had playlist function to check if the user even has a playlist
            if result:
                print("This is the number of song in your playlist: ", result)
            else:
                print("You haven't added any songs yet.")

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
