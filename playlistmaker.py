import random

import psycopg2
from sshtunnel import SSHTunnelForwarder

import program_vars
import sensitive
import landing

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
            query = "INSERT INTO playlist(playlistid, name, duration, " \
                    "quantity, " \
                    "isprivate) VALUES (%s, %s, %s, %s, %s)"
            vals = (p_id, p_name, 0, 0, p_privacy)

            curs.execute(query, vals)

            command = ""
            while True:
                print(
                    "commands:\n"
                    "\t add (pick one: song/album) {name}\n"
                    "\t delete (pick one: song/album) {name}\n"
                    "\t done\n")
                command = input(">")
                if command == "done":
                    break
                command = command.strip().split()
                name = ' '.join(map(str, command[2:]))

                if command[0] == "add":
                    if command[1] == "album":
                        # get albumid and duration
                        curs.execute(
                            "SELECT albumid, length FROM ALBUM "
                            "WHERE name = %s", (name,))
                        result = curs.fetchone()
                        album_id = result[0]
                        album_length = result[1]

                        # insert new relation
                        add_query = "INSERT INTO playlist_has_song(" \
                                    "playlistid, songid) " \
                                    "SELECT %s, songid FROM album_hasa_song " \
                                    "WHERE albumid = %s"
                        vals = (p_id, album_id)
                        curs.execute(add_query, vals)
                        conn.commit()

                        # get num of songs in album
                        count_query = "SELECT COUNT(albumid) " \
                                      "FROM album_hasa_song " \
                                      "WHERE albumid = %s"
                        curs.execute(count_query, (album_id,))
                        conn.commit()

                        p_duration += album_length
                        p_quantity += curs.fetchone()[0]

                    elif command[1] == "song":
                        # get songid and duration
                        curs.execute(
                            "SELECT songid, length FROM SONG WHERE name = "
                            "%s",
                            (name,))
                        result = curs.fetchone()
                        songid = result[0]
                        songlength = result[1]

                        add_query = "INSERT INTO playlist_has_song(playlistid, " \
                                    "songid) VALUES (%s, %s)"
                        vals = (p_id, songid)
                        curs.execute(add_query, vals)
                        conn.commit()
                        p_quantity += 1
                        p_duration += songlength
                elif command[0] == "delete":
                    if command[1] == "album":
                        # get albumid and duration
                        curs.execute(
                            "SELECT albumid, length FROM ALBUM "
                            "WHERE name = %s", (name,))
                        result = curs.fetchone()
                        album_id = result[0]
                        album_length = result[1]

                        del_query = "DELETE FROM playlist_has_song " \
                                    "WHERE playlistid = %s and songid IN " \
                                    "(SELECT songid FROM album_hasa_song " \
                                    "WHERE albumid = %s)"
                        vals = (p_id, album_id)
                        curs.execute(del_query, vals)
                        conn.commit()

                        count_query = "SELECT COUNT(albumid) " \
                                      "FROM album_hasa_song " \
                                      "WHERE albumid = %s"


                        curs.execute(count_query, (p_id, album_id))
                        conn.commit()

                        p_quantity -= curs.fetchone()[0]
                        p_duration -= album_length

                    elif command[1] == "song":
                        # get songid and duration
                        curs.execute(
                            "SELECT songid, length FROM SONG WHERE name = "
                            "%s",
                            (name,))
                        result = curs.fetchone()
                        songid = result[0]
                        songlength = result[1]

                        add_query = "DELETE FROM playlist_has_song " \
                                    "WHERE playlistid = %s AND songid = %s"
                        vals = (p_id, songid)
                        curs.execute(add_query, vals)
                        conn.commit()
                        p_quantity -= 1
                        p_duration -= songlength

                # print playlist so far
                print()
                print(p_name + " | " + str(round(p_duration, 2)) + " mins | " +
                      str(p_quantity) + " song(s)")
                print("___________________________")
                print_query = """ 
                    SELECT name, artist FROM SONG
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
                                    "SET duration = %s, " \
                                    "quantity = %s " \
                                    "WHERE playlistid = %s"
                vals = (p_duration, p_quantity, p_id)
                curs.execute(update_playlist_q, vals)

            # build user has playlist relation
            user_id = program_vars.USER_ID
            user_query = "INSERT INTO listeners_owns_playlist(userid," \
                         "playlistid) VALUES (%s, %s)"
            vals = (user_id, p_id)
            curs.execute(user_query, vals)
            conn.commit()


        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed")
