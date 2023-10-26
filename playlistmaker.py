import random

import psycopg2
from sshtunnel import SSHTunnelForwarder

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
            print("welcome to the playlist maker!")
            p_id = random.randint(1000000, 9999999)
            p_name = input("Playlist Name: ")
            p_privacy = input("Private? (y/n): ")
            if p_privacy == 'y':
                p_privacy = True
            elif p_privacy == 'n':
                p_privacy = False
            p_duration = 0.00
            p_quantity = 0

            # insert playlist into the table w/ basic info
            query = "INSERT INTO playlist(playlistid, name, duration, quantity, " \
                    "isprivate) VALUES (%s, %s, %s, %s, %s)"
            vals = (p_id, p_name, None, None, p_privacy)

            curs.execute(query, vals)

            command = ""
            while command != "done":
                print(
                    "type 'add (songname/album)' or 'add (songname/album)' build your "
                    "playlist. type 'done' to save playlist")
                command = input()
                command = command.strip().split()
                song_name = ' '.join(map(str, command[1:]))

                # get songid and duplicate
                curs.execute("SELECT songid, duration FROM SONG WHERE title = "
                             "%s",
                             (song_name,))
                songid = curs.fetchone()[0]
                songdur = curs.fetchone()[1]

                if command[0] == "add":
                    # TODO: add entire albums

                    add_query = "INSERT INTO playlist_has_song(playlistid, " \
                                "songid) VALUES (%s, %s)"
                    vals = (p_id, songid)
                    curs.execute(add_query, vals)
                    conn.commit()
                    p_quantity += 1
                    p_duration += songdur

                if command[0] == "delete":
                    # TODO: delete entire albums

                    add_query = "DELETE FROM playlist_has_song" \
                                "WHERE playlistid = %s AND songid = %s"
                    vals = (p_id, songid)
                    curs.execute(add_query, vals)
                    conn.commit()
                    p_quantity -= 1
                    p_duration -= songdur

                # print playlist so far
                print_query = """
                    SELECT title, artist FROM SONG
                    WHERE songid IN ( 
                        SELECT songid FROM playlist_has_song
                        WHERE playlistid = %s
                    )
                """
                curs.execute(print_query, (p_id,))

                for row in curs.fetchall():
                    print(row[0] + " by " + row[1])

                # update duration and quantity of playlist
                update_playlist_q = "UPDATE playlist " \
                                    "SET duration = %s" \
                                    "SET quantity = %s" \
                                    "WHERE playlist_id = %s"
                vals = (p_duration, p_quantity, p_id)

            # TODO: build user has playlist relation

        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed")
