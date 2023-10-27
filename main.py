import subprocess
import sys

if __name__ == "__main__":
    # run landing login/signup
    subprocess.run([sys.executable, 'landing.py'])

    subprocess.run([sys.executable, 'homepage.py'])

    subprocess.run([sys.executable, 'playlistmaker.py'])


    print("main finished")

    #TODO: clear program_vars
