import psycopg2
from sshtunnel import SSHTunnelForwarder

import sensitive
import program_vars

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"


def follow_user(curs, user_id):
    user_email = input("To follow another user input their email: ")

    search_query = "SELECT userid FROM listeners WHERE email = %s"
    curs.execute(search_query, (user_email,))
    result = curs.fetchone()

    if result is not None:
        target_user_id = result[0]

        # Create a relation "user follows user" to make the current user follow the target user
        follow_query = "INSERT INTO listeners_follows_user (followerid, " \
                       "followingid) VALUES (%s, %s)"
        curs.execute(follow_query, (user_id, target_user_id))

        conn.commit()

        print(f"You are now following the user with email: {user_email}")
    else:
        print(f"No user found with the email: {user_email}")


def unfollow_user(curs, user_id):
    user_email = input("To unfollow a user, input their email: ")

    search_query = "SELECT userid FROM listeners WHERE email = %s;"
    curs.execute(search_query, (user_email,))
    result = curs.fetchone()

    if result is not None:
        target_user_id = result[0]

        # Remove the relation "user follows user" to unfollow the target user
        unfollow_query = "DELETE FROM listeners_follows_user WHERE followerid = %s AND followingid = %s;"
        curs.execute(unfollow_query, (user_id, target_user_id))

        conn.commit()

        print(f"You have unfollowed the user with email: {user_email}")
    else:
        print(f"No user found with the email: {user_email}")


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

        # DB work here....
        try:
            user_id =program_vars.USER_ID   # get user's real id
            action = input("Do you want to (F)ollow or (U)nfollow a user? ").upper()

            if action == 'F':
                follow_user(curs, user_id)
            elif action == 'U':
                unfollow_user(curs, user_id)
            else:
                print("Invalid action. Please enter 'F' to follow or 'U' to unfollow.")

        except Exception as e:  # debugging purposes
            print("User DB changes failed.")
            print(e)

        conn.commit()

        conn.close()
except:
    print("Connection failed")
