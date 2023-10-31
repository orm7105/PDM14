import psycopg2
from sshtunnel import SSHTunnelForwarder

import program_vars
import sensitive
from datetime import datetime
import landing

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"


def play_song(listener_id, song_id):
    """
    play_song() - 'Plays' a song given a songid and listenerid, and inserts a new row into the
        listeners_listensto_song table
    :param listener_id: the userid
    :param song_id: the songid
    """
    # Gets current date time as a string
    current_dt = datetime.now()
    dt_str = current_dt.strftime("%Y/%m/%d %H:%M:%S")

    # Query to be used in SQL
    query = "INSERT INTO listeners_listensto_song " \
            "VALUES (%s, %s, %s)"
    vals = (listener_id, song_id, dt_str)

    # Query Execution
    curs.execute(query, vals)


def play_playlist(listener_id, playlist_id):
    """
    play_playlist() - plays a playlist given a playlistid and userid, and inserts a row for every
        song in the playlist into listeners_listensto_song
    :param listener_id: the userid
    :param playlist_id: the playlistid
    """
    # Query and execution to get all songs in playlist
    query = "SELECT songid " \
            "FROM playlist_has_song " \
            "WHERE playlistid = %s"
    vals = (playlist_id,)
    curs.execute(query, vals)

    # Get songs and play each song
    song_tuple = curs.fetchall()
    for song_id in song_tuple:
        play_song(listener_id, song_id[0])


def count_song_played(listener_id, song_id):
    """
    count_song_played() - Counts the amount of time a song has been played by a user;
        derived from the listeners_listensto_song table
    :param listener_id: the userid
    :param song_id: the songid
    :return (int) the amount of times a user has played a song
    """
    # Query and Query Execution
    query = "SELECT COUNT(date_time) " \
            "FROM listeners_listensto_song " \
            "WHERE userid = %s AND songid = %s"
    vals = (listener_id, song_id)
    curs.execute(query, vals)

    count = curs.fetchone()
    return count


# Tries to connect to Server
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

        # Tries to search up a playlist or song
        try:

            while True:
                # UserID
                listener_id = program_vars.USER_ID

                print("Would you like to play a Song or Playlist (s/song/p/playlist)?")
                print("Type 'exit' to exit")
                user_input = input()

                # Play Song
                if user_input.lower() == 's' or user_input.lower() == "song":
                    # Song Query
                    song_name = input("Song Name: ")
                    # Needs artist because of song's with same name
                    song_artist = input("Song Artist: ")
                    song_id_query = "SELECT s.songid FROM song AS s " \
                                    "WHERE s.name = %s AND s.artist = %s"
                    vals = (song_name, song_artist)
                    curs.execute(song_id_query, vals)

                    # Fetches SongID
                    song_id = curs.fetchone()
                    # Plays song and inserts a new
                    if song_id is None:
                        print("Song cannot be found :(")
                    else:
                        play_song(listener_id, song_id[0])
                        print("Song played successfully!")

                        # Tells user how many times you have play this specific song
                        count = count_song_played(listener_id, song_id[0])
                        print("You have played this song " + str(count[0]) + " amount of time(s)!")

                # Play Playlist
                elif user_input.lower() == 'p' or user_input.lower() == "playlist":

                    # Playlist Query
                    playlist_name = input("Playlist Name: ")
                    playlist_id_query = "SELECT playlistid FROM playlist " \
                                        "WHERE name = %s"
                    playlist_vals = (playlist_name,)
                    curs.execute(playlist_id_query, playlist_vals)

                    # Fetches PlaylistID
                    playlist_id = curs.fetchone()
                    if playlist_id is None:
                        print("Playlist cannot be found :(")
                    else:
                        play_playlist(listener_id, playlist_id[0])
                        print("Playlist played successfully!")

                # Exit System
                elif user_input.lower() == 'exit':
                    print("Exit success!")
                    break

                # Unrecognized input
                else:
                    print("Invalid input, must input (s/song/p/playlist)")

        # Failed playing of playlist or song
        except Exception as e:
            print("Failed! Try again!")
            print(e)

        conn.commit()
        conn.close()

# Failed to connect, exit out
except Exception as e:
    print("Connection failed")