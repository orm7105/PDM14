import psycopg2
from sshtunnel import SSHTunnelForwarder

import program_vars
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
            # UserID
            listener_id = program_vars.USER_ID
            # gets the first name of the user
            curs.execute(f"""
                        SELECT firstname, lastname
                        FROM LISTENERS
                        WHERE userid = %s
                    """, (listener_id,))

            user_name = curs.fetchone()  # got the name RAHHHHHH
            first = user_name[0]
            last = user_name[1]

            print(f"Hi {first} {last}! Welcome to your profile page!")

            curs.execute(f"""
                        SELECT COUNT(playlistid)
                        FROM listeners_owns_playlist
                        WHERE userid = %s
                    """, (listener_id,))

            collection_count = curs.fetchone()
            collect = collection_count[0]
            print(f"You currently have {collect} playlists.")
            # number of subscribers you have
            # get the count of that user id from followingid
            curs.execute(f"""
                        SELECT COUNT(followingid)
                        FROM listeners_follows_user
                        WHERE followingid = %s
                    """, (listener_id,))

            follower_count = curs.fetchone()  # Fetch all matching rows
            follower = follower_count[0]
            print(f"You have {follower} followers!")
            # number of people you subscribe to
            # get the count of user id from followerid
            curs.execute(f"""
                        SELECT COUNT(followerid)
                        FROM listeners_follows_user
                        WHERE followerid = %s
                    """, (listener_id,))

            following_count = curs.fetchone()  # Fetch all matching rows
            following = following_count[0]
            print(f"You are following {following} users!")

            # the top 10 artists by most plays
            print("Here are your top 10 artists by the most plays:")
            # get the top 10 most played songs, using those songids, get the artist from them
            curs.execute(f"""
                        SELECT songid
                        FROM listeners_listensto_song
                        WHERE userid = %s
                        ORDER BY date_time DESC
                        LIMIT 10
                    """, (listener_id,))
            top_songs_played = curs.fetchall()
            i = 0
            for songs in top_songs_played:
                i += 1
                curs.execute(f"""
                            SELECT artist
                            FROM song
                            WHERE songid = %s
                        """, (songs,))
                a = curs.fetchone()
                artist = a[0]
                print(f"\t{i}. {artist}")
            p = 0
            # get the top 10 artists by most additions to playlists
            print("Here are your top 10 artists by the most addition to playlists:")
            # get all the playlists owned by a user
            curs.execute(f"""
                        SELECT playlistid
                        FROM listeners_owns_playlist
                        WHERE userid = %s
                    """, (listener_id,))
            playlists = curs.fetchall()
            # get all the songids in those playlists

            # dictionary to store artist counts
            artist_counts = {}
            s = 0
            for playlist in playlists:
                p += 1
                curs.execute(f"""
                            SELECT songid
                            FROM playlist_has_song
                            WHERE playlistid = %s
                        """, (playlist,))
                songids = curs.fetchall()
                for songid in songids:
                    s += 1
                    curs.execute(f"""
                                SELECT artist
                                FROM SONG
                                WHERE songid = %s
                            """, (songid,))
                    artist = curs.fetchone()

                    # counts instances of artists in the dictionary
                    if artist in artist_counts:
                        artist_counts[artist] += 1
                    else:
                        artist_counts[artist] = 1

            # does the sorting to get the top ten
            top_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            j = 0
            for artist, count in top_artists:
                j += 1
                print(f"\t{j}. {artist[0]}: {count} additions to playlists")

            # this is useful for testing purposes to double-check the num of playlist and num of songs are correct
            print(f"total songs: {s}")
            print(f"total playlists: {p}")











        except Exception as e:
            print("db edits failed")
            print(e)

        conn.commit()

        conn.close()

except:
    print("Connection failed\n")
