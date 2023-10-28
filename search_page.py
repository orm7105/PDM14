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

        # TODO make the search results print in an order
        try:
            print("Search for a song!")
            search_select = " "
            while search_select[0] != "exit":
                print("Search for a song by: \n- name\n- artist\n- album\n- genre\ntype 'exit' to exit\n")
                search_select = input()
                search_select = search_select.strip().split()
                search_element = ' '.join(map(str, search_select[1:]))  # what is being used to search
                checker = False
                if search_select[0] == "name":

                    # gets songid, artist, and length
                    curs.execute("""
                                SELECT S.songid, S.artist, S.length, A.name AS album_name
                                FROM SONG AS S
                                LEFT JOIN album_hasa_song AS AH ON S.songid = AH.songid
                                LEFT JOIN ALBUM AS A ON AH.albumid = A.albumid
                                WHERE S.name = %s
                                ORDER BY S.name ASC
                            """, (search_element,))

                    result = curs.fetchone()
                    # might need a for loop to loop through everything in results
                    if result:
                        songid = result[0]
                        song_artist = result[1]
                        song_length = result[2]
                        album_name = result[3]
                        print(f"Song Name: {search_element}, Artist: {song_artist}, Length: {song_length}, Album: {album_name}")
                    else:
                        print("Song not found.")

                if search_select[0] == "artist":
                    # searched the database for song by artist
                    curs.execute("""
                                SELECT A.artisid, S.name, S.artist, S.length, A.name AS album_name
                                FROM ARTIST AS A
                                LEFT JOIN album_hasa_song AS AH ON S.songid = AH.songid
                                LEFT JOIN ALBUM AS A ON AH.albumid = A.albumid
                                WHERE S.name = %s
                                ORDER BY S.name ASC
                            """, (search_element,))
                    curs.execute("""
                                SELECT S.songid, S.artist, S.length, A.name AS album_name
                                FROM SONG AS S
                                LEFT JOIN album_hasa_song AS AH ON S.songid = AH.songid
                                LEFT JOIN ALBUM AS A ON AH.albumid = A.albumid
                                WHERE S.name = %s
                                ORDER BY S.name ASC
                            """, (search_element,))

                if search_select[0] == "album":
                    # searches the database for song by album
                    print("searches by album")
                if search_select[0] == "genre":
                    # searches the database for song by genre
                    print("searches by genre")
                if search_select[0] == "exit":
                    print("exiting the search!")
                else:
                    print("in`valid search option, try again")
                # if checker:
                #     print_query = """
                #                         SELECT title, artist FROM SONG
                #                         WHERE songid IN (
                #                             SELECT songid FROM playlist_has_song
                #                             WHERE playlistid = %s
                #                         )
                #                     """
                #     curs.execute(print_query, (p_id,))



        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")
