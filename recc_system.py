import psycopg2
from sshtunnel import SSHTunnelForwarder
from datetime import datetime

import sensitive
import program_vars

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"
#Test #6

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

                user_input = input("Songs based on: \n[Enter exit to leave]\n")
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
                                            INNER JOIN listeners_listensto_song llts ON c.songid = llts.songid 
                                            WHERE c.songid = s.songid AND llts.date_time >= CURRENT_TIMESTAMP - INTERVAL '30 days')
                                        AS listen_count 
                                    FROM song AS s 
                                    LEFT OUTER JOIN artist_releasesa_song ars ON s.songid = ars.songid 
                                    LEFT OUTER JOIN artist art ON ars.artistid = art.artistid)
                                    AS topInfo 
                                    ORDER BY listen_count DESC 
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
                #  artist) and the play history of similar users

                elif user_input[0] == "4":
                    print("For you: Recommend songs to listen to based on your play history\n")
                    print("Title        Length         Release Date\n")
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
                    for artist in user_history_artist:
                        UHA_title = artist[0]
                        UHA_artist = artist[1]
                        UHA_album= artist[2]
                        UHA_release = artist[3]
                        UHA_length = artist[4]
                        print(UHA_title,", ", UHA_length,", ",UHA_release , "\n")

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
                    UHG_genre = curs.fetchall()

                    for each_genre in UHG_genre:
                        UHG_Name = each_genre[0]
                        UHG_artist= each_genre[1]
                        UHG_album = each_genre[2]
                        UHG_release = each_genre[3]
                        UHG_Length = each_genre[4]
                        print(UHG_Name, ", ",UHG_Length,", ", UHG_release, "\n")

                  # Find Similar Users:
                    # 1. They follow you
                    # 2. You follow them
                    # 3. They follow at least 2 of the same people that you are following
                    curs.execute(""" 
                        SELECT DISTINCT F1.followerid AS common_follower
                        FROM listeners_follows_user F1
                        JOIN listeners_follows_user F2 ON F1.followerid = F2.followerid
                        WHERE F1.followingid = %s
                        OR F1.followerid <> %s
                        OR F2.followingid = %s
                        OR F1.followerid IN (
                            SELECT DISTINCT followingid
                            FROM listeners_follows_user
                            WHERE followerid = %s
                            GROUP BY followingid
                            HAVING COUNT(DISTINCT followerid) >= 2
                        );
                    """, (listener_id,listener_id, listener_id, listener_id))
                    UH_similar_users = curs.fetchall()
                    similar_users = []
                    for users in UH_similar_users:
                        similar_users.append(users[0])


                    curs.execute("""
                        WITH TopArtists AS (
                            SELECT A.name, A.artistid
                            FROM listeners_listensto_song AS L
                            INNER JOIN artist_releasesa_song AS RS ON RS.songid = L.songid
                            INNER JOIN artist AS A ON A.artistid = RS.artistid
                            WHERE L.userid = ANY(%s)
                            GROUP BY A.name, A.artistid
                            LIMIT 10
                        ),
                        ArtistListenersCount AS (
                            SELECT
                                A.artistid,
                                COUNT(DISTINCT L.userid) AS listener_count
                            FROM
                                listeners_listensto_song AS L
                            INNER JOIN
                                artist_releasesa_song AS RS ON RS.songid = L.songid
                            INNER JOIN
                                artist AS A ON A.artistid = RS.artistid
                            WHERE
                                L.userid = ANY(%s)
                            GROUP BY
                                A.artistid
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
                        ORDER BY
                            (SELECT listener_count FROM ArtistListenersCount WHERE artistid = a.artistid) DESC
                        LIMIT 10;
                    """, (similar_users, similar_users))
                    similar_users_artist = curs.fetchall()
                    for similar in similar_users_artist:
                        SUA_title = similar[0]
                        SUA_length = similar[4]
                        SUA_release = similar[3]
                        print(SUA_title, ", ", SUA_length, ", ", SUA_release, "\n")




                elif (user_input[0] == "exit"):
                    break






        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")

