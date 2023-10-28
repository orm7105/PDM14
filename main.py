import subprocess
import sys

if __name__ == "__main__":
    # run landing login/signup
    subprocess.run([sys.executable, 'landing.py'])

    subprocess.run([sys.executable, 'homepage.py'])


    print("Thanks for using Aria no.14!")

    # clear program_vars
    with open('program_vars.py', 'w') as file:
        pass
