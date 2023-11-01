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
        params = {
            'database': dbName,
            'user': username,
            'password': password,
            'host': 'localhost',
            'port': server.local_bind_port
        }

        conn = psycopg2.connect(**params)
        curs = conn.cursor()

        try:
            print("           _____  _____          ")
            print("     /\   |  __ \|_   _|   /\    ")
            print("    /  \  | |__) | | |    /  \   ")
            print("   / /\ \ |  _  /  | |   / /\ \  ")
            print("  / ____ \| | \ \ _| |_ / ____ \ ")
            print(" /_/    \_\_|  \_\_____/_/    \_\\")
            print("                                 ")
            print("                                 ")

            print("------------------------")
            print("┬ ┬┌─┐┌┬┐┌─┐┌─┐┌─┐┌─┐┌─┐")
            print("├─┤│ ││││├┤ ├─┘├─┤│ ┬├┤ ")
            print("┴ ┴└─┘┴ ┴└─┘┴  ┴ ┴└─┘└─┘")
            print("------------------------")

            user_id = program_vars.USER_ID
            action = input("view all playlists (Y/N)?: ").upper()
            if action == 'Y':

                print("\n\n-------------")
                print("ALL PLAYLISTS")
                print("-------------")

                query = "SELECT name, quantity, duration FROM playlist " \
                        "WHERE playlistid IN (SELECT playlistid FROM " \
                        "listeners_owns_playlist " \
                        "WHERE userid = %s) ORDER BY name ASC"

                curs.execute(query, (user_id,))

                playlist = curs.fetchall()

                if playlist is None:
                    print("You have no playlists")

                for playlist in playlist:
                    name, quantity, duration = playlist
                    # print(f"Playlist Name: {name}")
                    # print(f"Number of Songs in Playlist: {quantity}")
                    # print(f"Total Duration in Minutes: {duration} minutes")
                    print(f"\t* {name} | {duration} mins | {quantity} song(s)")
            else:
                print("Ok!")
                conn.commit()

                conn.close()

            command = ""
            while True:
                print("\n\n\n\nYou are currently at the....")

                print("------------------------")
                print("┬ ┬┌─┐┌┬┐┌─┐┌─┐┌─┐┌─┐┌─┐")
                print("├─┤│ ││││├┤ ├─┘├─┤│ ┬├┤ ")
                print("┴ ┴└─┘┴ ┴└─┘┴  ┴ ┴└─┘└─┘")
                print("------------------------")

                print("commands:\n"
                      "\t make playlist >\n"
                      "\t search >\n"
                      "\t play music >\n"
                      "\t edit playlists >\n"
                      "\t edit following >\n"
                      "\t exit >\n")

                command = input(">")
                if command == "exit":
                    break

                command = command.strip()

                if command == "make playlist":
                    subprocess.run([sys.executable, 'playlistmaker.py'])
                elif command == "search":
                    subprocess.run([sys.executable, 'search_page.py'])
                elif command == "play music":
                    subprocess.run([sys.executable, 'playpage.py'])
                elif command == "edit following":
                    subprocess.run([sys.executable, 'followingpage.py'])
                elif command == "edit playlists":
                    subprocess.run([sys.executable, 'playlisteditor.py'])

        except Exception as e:  # debugging purposes
            print("user db changes failed.")
            print(e)

        conn.commit()

        conn.close()
except:
    print("Connection failed")
