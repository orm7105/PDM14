import subprocess
import sys

if __name__ == "__main__":
    # run landing login/signup
    subprocess.run([sys.executable, 'landing.py'])

    subprocess.run([sys.executable, 'homepage.py'])

    subprocess.run([sys.executable, 'followingpage.py'])


    print("main finished")

    # clear program_vars
    with open('program_vars.py', 'w') as file:
        pass
