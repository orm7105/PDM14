import psycopg2
from sshtunnel import SSHTunnelForwarder

import sensitive

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"


# Function to sort and print song records
def sort_and_print(song_info, key_index, reverse_order):
    song_info_sorted = sorted(song_info, key=lambda x: x[key_index], reverse=reverse_order)
    for song_record in song_info_sorted:
        song_name, artist_name, album_name, release_date, length = song_record
        print(
            f"Song: {song_name}, Artist: {artist_name}, Album: {album_name}, Release Date: {release_date}, Length: {length}")


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
                tempList =[]
                if search_select[0] == "exit":
                    print("exiting the search!")
                    break

                if search_select[0] == "name":

                    # gets songid, artist, and length
                    curs.execute(f"""
                                SELECT S.songid, S.artist,S.releasedate ,S.length, A.name AS album_name
                                FROM SONG AS S
                                LEFT JOIN album_hasa_song AS AH ON S.songid = AH.songid
                                LEFT JOIN ALBUM AS A ON AH.albumid = A.albumid
                                WHERE S.name = %s
                                ORDER BY S.name ASC, S.artist ASC;
                            """, (search_element,))

                    results = curs.fetchall()  # Fetch all matching rows
                    tempList = results

                    if results:
                        for result in results:
                            songid = result[0]
                            song_artist = result[1]
                            song_release = result[2]
                            song_length = result[3]
                            album_name = result[4]
                            print(
                                f"Song Name: {songid}, Artist: {song_artist},Album: {album_name},Release Date:{song_release}, Length: {song_length}, ")
                    else:
                        print("Song not found.")



                elif search_select[0] == "artist":
                    curs.execute("SELECT artistid FROM ARTIST WHERE name = %s", (search_element,))
                    result = curs.fetchone()

                    if result:
                        artistid = result[0]

                        curs.execute(f"SELECT name, length FROM SONG WHERE artist = %s ORDER BY name ASC",
                                     (search_element,))
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
                                            f"Song Name: {song_name}, Artist: {artist_name}, Album: {album_name},Length: {song_length}")
                        else:
                            print("No songs found for the artist.")
                    else:
                        print("Artist not found.")



                if search_select[0] == "album":
                    print("searches by album")
                    curs.execute(f"""
                                SELECT albumid, artist 
                                FROM ALBUM
                                WHERE Name = %s
                            """, (search_element,))
                    album_result = curs.fetchone()

                    if album_result:
                        album_id = album_result[0]
                        album_artist = album_result[1]

                        curs.execute(f"""
                            SELECT songid
                            FROM album_hasa_song
                            WHERE albumid = %s
                        """, (album_id,))
                        result = curs.fetchall()
                        for songid in result:
                            curs.execute(f"""
                                SELECT name, length
                                FROM SONG
                                WHERE songid = %s
                                ORDER BY name ASC;
                            """, (songid,))
                            result = curs.fetchone()
                            if result:
                                song_name = result[0]
                                song_length = result[1]
                                print(
                                    f"Song: {song_name}, Artist: {album_artist}, Album Name: {search_element}, Length: {song_length}")
                    else:
                        print("Song not found.")


                if search_select[0] == "genre":
                    print("searches by genre")
                    curs.execute("SELECT genreid FROM GENRE WHERE genrename = %s", (search_element,))
                    result = curs.fetchone()

                    if result:
                        genreid = result[0]
                        genre_name = search_element
                        curs.execute("SELECT songid FROM song_hasa_genre WHERE genreid = %s",
                                     (genreid,))
                        song_ids = curs.fetchall()
                        song_id_list = [row[0] for row in song_ids]
                        if song_ids:
                            query = """
                                        SELECT song.name, song.artist, album.name, song.releasedate, song.length
                                        FROM song
                                        JOIN album_hasa_song ON song.songid = album_hasa_song.songid
                                        JOIN album ON album_hasa_song.albumid = album.albumid
                                        WHERE song.songid IN %s
                                        ORDER BY song.name ASC;
                                        """
                            curs.execute(query, (tuple(song_id_list),))
                            song_info = curs.fetchall()
                            tempList = song_info
                            for song_record in song_info:
                                song_name, artist_name, album_name, release_date, length = song_record
                                print(
                                    f"Song:{song_name},Album:{album_name}, Artist:{artist_name}, Release Date:{release_date}, Length:{length}")
                        #songInfo


    #Sort based on users input

                print("\nSort by: song name -s , artist’s name -a , genre -g ,and released year -r")
                sort_input = input().strip()
                category = sort_input[0]

                print("Sort Ascending or Descending: - ASC - DESC ")
                sort_order = input().strip()
                reverse_order = sort_order[0].upper() == 'D'

                if category == 'a':
                    sort_and_print(tempList, 1, reverse_order)  # Sort by artist name
                elif category == 's':
                    sort_and_print(tempList, 0, reverse_order)  # Sort by song name
                elif category == 'r':
                    # Filter out records with None release dates
                    song_info_filtered = [record for record in tempList if record[3] is not None]
                    sort_and_print(song_info_filtered, 3, reverse_order)  # Sort by release year



        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")
