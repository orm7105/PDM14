import random

import psycopg2
from sshtunnel import SSHTunnelForwarder

import program_vars
import sensitive

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"

try:
    def edit_playlist(p_name):
        while True:

            # print existing playlist
            print_query = "SELECT * FROM playlist " \
                        "WHERE playlistid IN (SELECT playlistid FROM " \
                          "listeners_owns_playlist " \
                            "WHERE userid = %s)"
            curs.execute(print_query, (user_id,))

            p = curs.fetchone()
            p_id = p[0]
            p_duration = p[2]
            p_quantity = p[3]

            print()
            print(p[1] + " | " + str(round(p_duration, 2)) + " mins | " +
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


        # print commands
            print(
                "commands:\n"
                "\t edit name \n"
                "\t add (pick one: song/album) {name}\n"
                "\t delete (pick one: song/album) {name}\n"
                "\t done\n")
            command = input(">")
            if command == "done":
                break
            elif command == "edit name":
                new_name = input("enter new playlist name: ")
                rename_query = "UPDATE playlist " \
                               "SET name = %s " \
                               "WHERE playlistid = %s"
                vals = (new_name, p_id)
                curs.execute(rename_query, vals)
                conn.commit()
                continue

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

                    # update quantity and duration
                    count_query = "SELECT COUNT(albumid) " \
                                  "FROM album_hasa_song " \
                                  "WHERE albumid = %s"
                    curs.execute(count_query, (album_id,))
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

            # update duration and quantity of playlist
            update_playlist_q = "UPDATE playlist " \
                                "SET duration = %s, " \
                                "quantity = %s " \
                                "WHERE playlistid = %s"
            vals = (p_duration, p_quantity, p_id)
            curs.execute(update_playlist_q, vals)




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

            while True:
                print("----playlist editor----")
                print()
                print("your playlists: \n")
                print()
                user_id = program_vars.USER_ID
                query = "SELECT name, quantity, duration FROM playlist " \
                        "WHERE playlistid IN (SELECT playlistid FROM listeners_listensto_playlist " \
                        "WHERE userid = %s)"

                curs.execute(query, (user_id,))

                playlist = curs.fetchall()

                if playlist is None:
                    print("You have no playlists")

                for playlist in playlist:
                    name, quantity, duration = playlist
                    print(f"Playlist Name: {name}")
                    print(f"Number of Songs in Playlist: {quantity}")
                    print(f"Total Duration in Minutes: {duration} minutes")

                command = ""

                print(
                    "commands:\n"
                    "\t edit {playlist name}\n"
                    "\t delete {playlist name}\n"
                    "\t done\n")
                command = input(">")
                if command == "done":
                    break

                command = command.strip().split()
                p_name = ' '.join(map(str, command[1:]))
                if command[0] == "edit":
                    edit_playlist(p_name)

                elif command[0] == "delete":
                    confirm = input("You are about to delete \"" + p_name +
                          "\". Continue? (y/n) : ")
                    if confirm == "y":
                        del_query = "DELETE FROM playlists " \
                                    "WHERE creator = %s AND name = %s"
                        vals = (user_id, p_name)
                        curs.execute(del_query, vals)
                        conn.commit()

                        print("\"" + p_name + "\"" + " was deleted.")











        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed")
