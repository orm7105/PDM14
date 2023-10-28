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

        # TODO Users can sort the resulting list by song name, artist’s name, genre and released year (ascending and descending)
        try:
            print("Search for a song!")
            search_select = " "
            while search_select[0] != "exit":
                print("Search for a song by: \n- name\n- artist\n- album\n- genre\ntype 'exit' to exit\n")
                search_select = input()
                search_select = search_select.strip().split()
                search_element = ' '.join(map(str, search_select[1:]))  # what is being used to search
                print("Sort Ascending or Descending: - ASC - DESC ")
                sort = input()
                user_order = sort.strip().split()
                sort_order = user_order[0]



            #DOUBLE CHECK IT WORKS
                checker = False
                if search_select[0] == "name":

                    # gets songid, artist, and length
                    curs.execute(f"""
                                SELECT S.songid, S.artist, S.length, A.name AS album_name
                                FROM SONG AS S
                                LEFT JOIN album_hasa_song AS AH ON S.songid = AH.songid
                                LEFT JOIN ALBUM AS A ON AH.albumid = A.albumid
                                WHERE S.name = %s
                                ORDER BY S.name {sort_order}
                            """, (search_element,))

                    results = curs.fetchall()  # Fetch all matching rows

                    if results:
                        for result in results:
                            songid = result[0]
                            song_artist = result[1]
                            song_length = result[2]
                            album_name = result[3]
                            print(
                                f"Song Name: {search_element}, Artist: {song_artist}, Length: {song_length}, Album: {album_name}")
                    else:
                        print("Song not found.")

                elif search_select[0] == "artist":
                    # searched the database for song by artist
                    curs.execute("SELECT artistid FROM ARTIST WHERE name = %s", (search_element,))
                    result = curs.fetchone()

                    if result:
                        artistid = result[0]

                        curs.execute(f"SELECT name, length FROM SONG WHERE artist = %s ORDER BY name  {sort_order}", (search_element,))
                        songs = curs.fetchall()

                        if songs:
                            artist_name = search_element

                            for song in songs:
                                song_name = song[0]
                                song_length = song[1]

                                curs.execute("SELECT albumid FROM artist_releasesa_album WHERE artistid = %s",
                                             (artistid,))
                                result = curs.fetchone()

                                if result:
                                    albumid = result[0]

                                    curs.execute("SELECT name FROM ALBUM WHERE albumid = %s", (albumid,))
                                    result = curs.fetchone()

                                    if result:
                                        album_name = result[0]
                                        print(
                                            f"Song Name: {song_name}, Artist: {artist_name}, Length: {song_length}, Album: {album_name}")
                        else:
                            print("No songs found for the artist.")
                    else:
                        print("Artist not found.")

                if search_select[0] == "album":
                    # searches the database for song by album
                    print("searches by album")
                    curs.execute(f"""
                                SELECT name, artist, length, releasedate
                                FROM ALBUM
                                WHERE Name = %s
                                ORDER BY artist {sort_order};

                            """, (search_element,))
                    album_result = curs.fetchone()
                    # might need a for loop to loop through everything in results
                    if album_result:
                        album_id = album_result[0]
                        album_artist = album_result[1]
                        album_length = album_result[2]
                        album_release = album_result[3]
                        print(
                            f"Song Name: {search_element}, Artist: {album_artist}, Length: {album_length}, Release Date: {album_release}")
                    else:
                        print("Song not found.")


                if search_select[0] == "genre":
                    # searches the database for song by genre

                    print("searches by genre")
                    curs.execute("SELECT genreid FROM GENRE WHERE genrename = %s", (search_element,))
                    result = curs.fetchone()

                    if result:
                        genreid = result[0]
                        genre_name = search_element
                        #Search for a Song that belongs to a genre
                        curs.execute("SELECT songid FROM song_hasa_genre WHERE genreid = %s",
                                             (genreid,))
                        song_ids = curs.fetchall()

                        if song_ids:
                            for song_id in song_ids:
                                song_id = song_id[0]  # Extract the value from the tuple
                                curs.execute(f"SELECT name, artist, releasedate, length FROM SONG WHERE songid = %s  ORDER BY artist {sort_order}",
                                             (song_id,))
                                song_info = curs.fetchone()

                                # Search for albumid of said song
                                curs.execute("SELECT albumid FROM album_hasa_song WHERE songid = %s",
                                             (song_id,))
                                song_album_id = curs.fetchone()
                                 #get the name of said album
                                curs.execute("SELECT name  FROM ALBUM WHERE albumid = %s ",
                                             (song_album_id,))
                                album_genre_name = curs.fetchone()

                                if song_info:
                                    song_name = song_info[0]
                                    artist_name = song_info[1]
                                    release_date = song_info[2]
                                    length = song_info[3]
                                if album_genre_name:
                                    album_gname= album_genre_name[0]
                                    print(f"Song:{song_name},Artist: {artist_name},Album: {album_gname} , Release Date: { release_date} , Length:{length} ")
                    else:
                        print("Genre Not Found")


                if search_select[0] == "exit":
                    print("exiting the search!")
                else:
                    print("in`valid search option, try again")


        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")
