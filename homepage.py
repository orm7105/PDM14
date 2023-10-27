import random
import subprocess
import sys

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
            print("\n\n\nWelcome to the Homepage!")

            command = ""
            while True:
                user_id = program_vars.USER_ID

                query = "SELECT name, quantity, duration FROM playlist " \
                        "WHERE playlistid IN (SELECT playlistid FROM listeners_listensto_playlist " \
                        "WHERE userid = %s)"

                curs.execute(query, (user_id,))

                playlist = curs.fetchall()

                for playlist in playlist:
                    name, quantity, duration = playlist
                    print(f"Playlist Name: {name}")
                    print(f"Number of Songs in Playlist: {quantity}")
                    print(f"Total Duration in Minutes: {duration} minutes")


                # Top artists
                # Users following
                # Link to create playlist

                print("commands:\n"
                      "\t make playlist >\n"
                      "\t search >\n"
                      "\t edit playlists >\n"
                      "\t edit following >" 
                      "\t exit >\n")

                command = input(">")
                if command == "exit":
                    break

                command = command.strip()

                if command == "make playlist":
                    subprocess.run([sys.executable, 'playlistmaker.py'])
                elif command == "search":
                    subprocess.run([sys.executable, 'search_page.py'])
                elif command == "edit following":
                    subprocess.run([sys.executable, 'followingpage.py'])


                # elif command == "search":
                #     subprocess.run([sys.executable, 'playlist_editor.py'])
        except Exception as e:  # debugging purposes
            print("user db changes failed.")
            print(e)

        conn.commit()

        conn.close()
except:
    print("Connection failed")
