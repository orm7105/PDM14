import subprocess
import sys

if __name__ == "__main__":
    # run landing login/signup
    subprocess.run([sys.executable, 'landing.py'])

    # run home page
    subprocess.run([sys.executable, 'homepage.py'])




    print("main finished")
