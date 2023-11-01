import psycopg2
from sshtunnel import SSHTunnelForwarder

import sensitive

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"
#Test to see changes
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
    return count[0]

# Function to sort and print song records
def sort_and_print(song_info, key_index, reverse_order):
    song_info_sorted = sorted(song_info, key=lambda x: x[key_index], reverse=reverse_order)
    for song_record in song_info_sorted:
        song_name, artist_name, album_name, release_date, length ,songid = song_record
        print(
            f"Song: {song_name}, Artist: {artist_name}, Album: {album_name}, Release Date: {release_date}, Length: {length}, Listen Count: {count_song_played(songid)}")


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
                                SELECT S.name, S.artist,A.name AS album_name, S.releasedate ,S.length,S.songid
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
                            songname = result[0]
                            song_artist = result[1]
                            song_release = result[3]
                            song_length = result[4]
                            album_name = result[2]
                            songid = result[5]
                            song_count = count_song_played(songid)
                            print(
                                f"Song Name: {songname}, Artist: {song_artist},Album: {album_name}, Release Date:{song_release}, Length: {song_length}, Listen Count: {song_count}")
                    else:
                        print("Song not found.")



                elif search_select[0] == "artist":
                    curs.execute("""
                        SELECT s.name AS song_name, a.name AS artist_name,al.name AS album_name,s.releasedate,s.length,s.songid
                        FROM SONG s
                        JOIN ARTIST a ON s.artist = a.name
                        LEFT JOIN artist_releasesa_album ara ON a.artistid = ara.artistid
                        LEFT JOIN ALBUM al ON ara.albumid = al.albumid
                        WHERE a.name = %s
                        ORDER BY s.name ASC
                    """, (search_element,))

                    results = curs.fetchall()
                    tempList = results

                    if results:
                        for result in results:
                            song_name = result[0]
                            song_length = result[4]
                            songid = result[5]
                            artist_name = result[1]
                            album_name = result[2]
                            release = result[3]

                            print(
                                f"Song: {song_name}, Artist: {artist_name}, Album: {album_name}, Length: {song_length}, Release Date: {release} Listen Count: {count_song_played(songid)}")
                    else:
                        print("No songs found for the artist.")
                else:
                    print("Artist not found.")

                # fshdla
                # fasjfkdlj
                if search_select[0] == "album":
                    print("Searching by album")
                    curs.execute(f"""
                                        SELECT S.name AS song_name, A.artist AS album_artist, A.Name AS album_name, S.length,S.releasedate, S.songid
                                        FROM ALBUM AS A
                                        LEFT JOIN album_hasa_song AS AH ON A.albumid = AH.albumid
                                        LEFT JOIN SONG AS S ON AH.songid = S.songid
                                        WHERE A.Name = %s
                                        ORDER BY S.name ASC;
                                    """, (search_element,))

                    results = curs.fetchall()
                    tempList = results

                    if results:
                        for result in results:
                            song_name = result[0]
                            album_artist = result[1]
                            album_name = result[2]
                            song_length = result[3]
                            song_releasedate = result[4]
                            songid = result[5]
                            song_count = count_song_played(songid)

                            print(
                                f"Song: {song_name}, Artist: {album_artist}, Album Name: {album_name}, Length: {song_length},Release Date: {song_releasedate}, Listen Count: {song_count}")
                    else:
                        print("Album not found.")

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
                                        SELECT song.name, song.artist, album.name, song.releasedate, song.length, song.songid
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
                                song_name, artist_name, album_name, release_date, length, songid = song_record
                                print(
                                    f"Song:{song_name},Album:{album_name}, Artist:{artist_name}, Release Date:{release_date}, Length:{length}, Listen Count: {count_song_played(songid)}")
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
