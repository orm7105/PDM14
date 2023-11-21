import psycopg2
from sshtunnel import SSHTunnelForwarder
from datetime import datetime

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
            print("You are currently at the...")
            print('''\
  ____                                                   _       _   _              
 |  _ \ ___  ___ ___  _ __ ___  _ __ ___   ___ _ __   __| | __ _| |_(_) ___  _ __   
 | |_) / _ \/ __/ _ \| '_ ` _ \| '_ ` _ \ / _ \ '_ \ / _` |/ _` | __| |/ _ \| '_ \  
 |  _ <  __/ (_| (_) | | | | | | | | | | |  __/ | | | (_| | (_| | |_| | (_) | | | | 
 |_| \_\___|\___\___/|_| |_| |_|_| |_| |_|\___|_| |_|\__,_|\__,_|\__|_|\___/|_| |_| 
                                                                                          
                                                                                       
                        ''')

            print("Reccomendation based on: ")
            print("_______________________________________________________________________")
            print(" 1 - Top 50 most popular songs in the last 30 days  (rolling)")
            print(" 2 - Top 50 most popular songs among my followers")
            print(" 3 - Top 5 most popular genres of the month (calendar month)")
            print(" 4 - For you: Recommend songs to listen to based on your play history ")
            print("_______________________________________________________________________\n")
            search_select = " "

            while True:
                # Current UserID
                listener_id = program_vars.USER_ID

                # Gets current date time as a string
                current_dt = datetime.now()
                dt_str = current_dt.strftime("%Y/%m/%d %H:%M:%S")

                user_input = input("Songs based on: \n")
                print("Enter exit to leave")
                user_input = user_input.strip().split()

                #The top 50 most popular songs in the last 30 days (rolling)
                #Working
                if (user_input[0] == "1"):
                    print("Top 50 most popular songs in the last 30 days  (rolling)")
                    curs.execute("""
                                    SELECT * FROM (
                                    SELECT DISTINCT ON (s.name) 
                                        s.songid, 
                                        s.name, 
                                        s.length, 
                                        s.releasedate, 
                                        art.artistid, 
                                        art.name, 
                                            (SELECT COUNT(c) 
                                            FROM song AS c 
                                            INNER JOIN listeners_listensto_song ults ON c.songid = ults.songid 
                                            WHERE c.songid = s.songid AND ults.date_time >= CURRENT_TIMESTAMP - INTERVAL '30 days')
                                        AS listen_count 
                                    FROM song AS s 
                                    LEFT OUTER JOIN artist_releasesa_song ars ON s.songid = ars.songid 
                                    LEFT OUTER JOIN artist art ON ars.artistid = art.artistid)
                                    AS topInfo 
                                    ORDER BY listen_count ASC 
                                    LIMIT 50;
                                                 """, (listener_id,))
                    popular_song = curs.fetchall()
                    print("Title        Length         Release Date\n")
                    for song in popular_song:
                        title = song[1]
                        length = song[2]
                        release= song[3]
                        print(title,", ", length,", ",release,"\n")


                # The top 50 most popular songs among my followers
                elif(user_input[0] == "2"):
                    print("Top 50 most popular songs among my followers")
                    curs.execute("""
                                SELECT 
                                    song.songid, 
                                    song.name, 
                                    song.releasedate, 
                                    song.length,
                                    COUNT(*) AS listen_count
                                FROM song
                                INNER JOIN listeners_listensto_song ON song.songid = listeners_listensto_song.songid
                                INNER JOIN listeners_follows_user ON listeners_listensto_song.userid = listeners_follows_user.followerid
                                WHERE listeners_follows_user.followingid = %s
                                GROUP BY 
                                    song.songid, 
                                    song.name, 
                                    song.releasedate, 
                                    song.length
                                ORDER BY listen_count DESC
                                LIMIT 50;
                                 """, (listener_id,))
                    followers_song = curs.fetchall()
                    print("Title        Length         Release Date\n")

                    for pop_among in followers_song:
                        FS_title = pop_among[1]
                        FS_release = pop_among[2]
                        FS_length = pop_among[3]
                        print(FS_title, ", ", FS_length, ", ", FS_release, "\n")



                # The top 5 most popular genres of the month (calendar month)
                #WORKS
                elif (user_input[0] == "3"):
                    print("Top 5 Most Popular Genres of the Month")

                    curs.execute("""
                                SELECT genre.genrename, genre.genreid, COUNT(song.name) AS top
                                FROM genre 
                                JOIN song_hasa_genre ON genre.genreid = song_hasa_genre.genreid
                                JOIN song ON song.songid = song_hasa_genre.songid
                                JOIN listeners_listensto_song ON song.songid = listeners_listensto_song.songid
                                WHERE EXTRACT(MONTH FROM listeners_listensto_song.date_time) = EXTRACT(MONTH FROM CURRENT_TIMESTAMP)
                                AND EXTRACT(YEAR FROM listeners_listensto_song.date_time) = EXTRACT(YEAR FROM CURRENT_TIMESTAMP)
                                GROUP BY genre.genrename, genre.genreid
                                ORDER BY top DESC
                                LIMIT 5;
                                 """, (listener_id,))
                    popular_genre = curs.fetchall()
                    print("Genre: \n")

                    for genre in popular_genre:
                        name = genre[0]
                        print(name)

                #  For you: Recommend songs to listen to based on your play history (e.g. genre,
                #  artist) and [the play history of similar users] - Not finished

                elif user_input[0] == "4":
                    print("For you: Recommend songs to listen to based on your play history\n")
                    #Songs based on the top artist the user listens to
                    curs.execute("""
                                WITH TopArtists AS (
                                SELECT A.name, A.artistid
                                FROM listeners_listensto_song AS L
                                INNER JOIN artist_releasesa_song AS RS ON RS.songid = L.songid
                                INNER JOIN artist AS A ON A.artistid = RS.artistid
                                WHERE L.userid = %s
                                GROUP BY A.name, A.artistid
                                LIMIT 10
                            )
                            SELECT 
                                s.name AS song_name, 
                                a.name AS artist_name,
                                al.name AS album_name,
                                s.releasedate,
                                s.length,
                                s.songid
                            FROM 
                                SONG s
                            JOIN 
                                ARTIST a ON s.artist = a.name
                            LEFT JOIN 
                                artist_releasesa_album ara ON a.artistid = ara.artistid
                            LEFT JOIN 
                                ALBUM al ON ara.albumid = al.albumid
                            WHERE 
                                a.artistid IN (SELECT artistid FROM TopArtists)
                            LIMIT 10;

                                 """, (listener_id,))
                    user_history_artist = curs.fetchall()
                    print(user_history_artist)

                    #Top 5 Genres based on user history

                    curs.execute(""" 
                            WITH TopGenres AS (
                                SELECT 
                                    genre.genrename, 
                                    gn.genreid
                                FROM 
                                    genre 
                                INNER JOIN (
                                    SELECT 
                                        genreid, 
                                        COUNT(*) AS genre_count 
                                    FROM 
                                        song_hasa_genre 
                                    WHERE 
                                        songid IN (
                                            SELECT 
                                                songid 
                                            FROM 
                                                listeners_listensto_song 
                                            WHERE 
                                                userid = %s
                                        ) 
                                    GROUP BY 
                                        genreid
                                ) AS gn ON gn.genreid = genre.genreid 
                                LIMIT 5
                            )
                            SELECT
                                S.name AS song_name,
                                A.name AS artist_name,
                                AL.name AS album_name,
                                S.releasedate,
                                S.length,
                                S.songid
                            FROM
                                SONG AS S
                            JOIN
                                song_hasa_genre AS SHG ON S.songid = SHG.songid
                            JOIN
                                GENRE AS G ON SHG.genreid = G.genreid
                            JOIN
                                ARTIST AS A ON S.artist = A.name
                            LEFT JOIN
                                album_hasa_song AS AH ON S.songid = AH.songid
                            LEFT JOIN
                                ALBUM AS AL ON AH.albumid = AL.albumid
                            JOIN
                                TopGenres AS TG ON G.genreID = TG.genreid
                            LIMIT 10;
                                """, (listener_id,))
                    combo = curs.fetchall()
                    print(combo)











                elif (user_input[0] == "exit"):
                    break






        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")

