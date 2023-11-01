import subprocess
import sys
import os

if __name__ == "__main__":
    # run landing login/signup
    subprocess.run([sys.executable, 'landing.py'])

    print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n')

    subprocess.run([sys.executable, 'homepage.py'])



    print("main finished")

    # clear program_vars
    with open('program_vars.py', 'w') as file:
        pass
