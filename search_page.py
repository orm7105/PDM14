import psycopg2
from sshtunnel import SSHTunnelForwarder

import sensitive

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"

def count_song_played(song_id):
    """
    count_song_played() - Counts the amount of time a song has been played in total;
        derived from the listeners_listensto_song table
    :param song_id: the songid
    :return (int) the amount of times a user has played a song
    """
    # Query and Query Execution
    query = "SELECT COUNT(date_time) " \
            "FROM listeners_listensto_song " \
            "WHERE songid = %s"
    vals = (song_id,)
    curs.execute(query, vals)

    count = curs.fetchone()
    return count

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
                if search_select[0] == "exit":
                    print("exiting the search!")
                    break

                print("Sort Ascending or Descending: - ASC - DESC ")
                sort = input()
                user_order = sort.strip().split()
                sort_order = user_order[0]

                if search_select[0] == "name":

                    # gets songid, artist, and length
                    curs.execute(f"""
                                SELECT S.songid, S.artist, S.length, A.name AS album_name
                                FROM SONG AS S
                                LEFT JOIN album_hasa_song AS AH ON S.songid = AH.songid
                                LEFT JOIN ALBUM AS A ON AH.albumid = A.albumid
                                WHERE S.name = %s
                                ORDER BY S.artist {sort_order}
                            """, (search_element,))

                    results = curs.fetchall()  # Fetch all matching rows

                    if results:
                        for result in results:
                            songid = result[0]
                            song_artist = result[1]
                            song_length = result[2]
                            album_name = result[3]
                            song_count = count_song_played(songid)
                            print(
                                f"Song Name: {search_element}, Artist: {song_artist}, Length: {song_length}, Album: {album_name}, Listen Count: {song_count}")
                    else:
                        print("Song not found.")

                elif search_select[0] == "artist":
                    curs.execute("SELECT artistid FROM ARTIST WHERE name = %s", (search_element,))
                    result = curs.fetchone()

                    if result:
                        artistid = result[0]

                        curs.execute(f"SELECT name, length, songid FROM SONG WHERE artist = %s ORDER BY name  {sort_order}",
                                     (search_element,))
                        songs = curs.fetchall()

                        if songs:
                            artist_name = search_element

                            for song in songs:
                                song_name = song[0]
                                song_length = song[1]
                                songid = song[2]

                                curs.execute("SELECT albumid FROM artist_releasesa_album WHERE artistid = %s",
                                             (artistid,))
                                result = curs.fetchone()

                                if result:
                                    albumid = result[0]

                                    curs.execute("SELECT name FROM ALBUM WHERE albumid = %s", (albumid,))
                                    result = curs.fetchone()

                                    if result:
                                        album_name = result[0]
                                        song_count = count_song_played(songid)
                                        print(
                                            f"Song Name: {song_name}, Artist: {artist_name}, Length: {song_length}, Album: {album_name}, Listen Count: {song_count}")
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
                                ORDER BY length {sort_order};
                            """, (songid,))
                            result = curs.fetchone()
                            if result:
                                song_name = result[0]
                                song_length = result[1]
                                song_count = count_song_played(songid)
                                print(
                                    f"Album Name: {search_element}, Song: {song_name}, Artist: {album_artist}, Length: {song_length}, Listen Count: {song_count}")
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
                            if sort_order == "ASC":
                                query = """
                                        SELECT song.name, song.artist, album.name, song.releasedate, song.length, song.songid
                                        FROM song
                                        JOIN album_hasa_song ON song.songid = album_hasa_song.songid
                                        JOIN album ON album_hasa_song.albumid = album.albumid
                                        WHERE song.songid IN %s
                                        ORDER BY song.name ASC;
                                        """
                            else:
                                query = """
                                    SELECT song.name, song.artist, album.name, song.releasedate, song.length, song.songid
                                    FROM song
                                    JOIN album_hasa_song ON song.songid = album_hasa_song.songid
                                    JOIN album ON album_hasa_song.albumid = album.albumid
                                    WHERE song.songid IN %s
                                    ORDER BY song.name DESC;
                                    """
                            curs.execute(query, (tuple(song_id_list),))
                            song_info = curs.fetchall()
                            for song_record in song_info:
                                song_name, artist_name, album_name, release_date, length, songid = song_record
                                print(
                                    f"Song:{song_name}, Artist:{artist_name}, Album:{album_name}, Release Date:{release_date}, Length:{length}, Listen Count: {count_song_played(songid)}")


        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")
