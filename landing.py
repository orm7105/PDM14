import datetime
import random

import psycopg2
from sshtunnel import SSHTunnelForwarder

import sensitive

username = sensitive.get_user()
password = sensitive.get_pass()
dbName = "p320_14"


if __name__ == '__main__':
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

            # DB work here....
            try:
                existing_user = input("Existing user? (y/n): ")
                u_email = input("Email: ")
                u_pass = input("Password: ")
                current_date = datetime.datetime.now().isoformat()

                if existing_user == 'n':
                    first_name = input("First name: ")
                    last_name = input("Last name: ")

                    user_id = random.randint(1000000, 9999999)
                    with open('program_vars.py', 'a') as file:
                        file.write("USER_ID = " + str(user_id) + "\n")

                    query = "INSERT INTO listeners(userid, email, password, " \
                            "firstname, lastname, creationdate, lastaccessdate) " \
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    vals = (user_id, u_email, u_pass, first_name, last_name,
                            current_date, current_date)

                    print(vals)

                    curs.execute(query, vals)
                    conn.commit()
                elif existing_user == 'y':
                    # update last access date
                    update_query = """
                        UPDATE listeners
                        SET lastaccessdate = %s
                        WHERE email = %s
                    """
                    vals = (current_date, u_email)
                    curs.execute(update_query, vals)

                    # get user_id
                    curs.execute("SELECT userid FROM listeners WHERE email = "
                            "%s", (u_email,))
                    user_id = curs.fetchone()[0]
                    with open('program_vars.py', 'a') as file:
                        file.write("USER_ID = " + str(user_id) + "\n")


            except Exception as e:  # debugging purposes
                print("user db changes failed.")
                print(e)

            conn.commit()

            conn.close()
    except:
        print("Connection failed")
