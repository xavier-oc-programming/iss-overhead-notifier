import os
import sys
import subprocess
from pathlib import Path
from art import LOGO

ORIGINAL = Path(__file__).parent / "original" / "main.py"
ADVANCED = Path(__file__).parent / "advanced" / "main.py"

clear = True
while True:
    if clear:
        os.system("cls" if os.name == "nt" else "clear")
    clear = True
    print(LOGO)
    print("ISS Overhead Notifier — choose a build:")
    print("  1. Original  (course build)")
    print("  2. Advanced  (OOP refactor)")
    print("  q. Quit")
    choice = input("\nEnter choice: ").strip().lower()

    if choice == "1":
        subprocess.run([sys.executable, str(ORIGINAL)], cwd=str(ORIGINAL.parent))
        input("\nPress Enter to return to menu...")
    elif choice == "2":
        subprocess.run([sys.executable, str(ADVANCED)], cwd=str(ADVANCED.parent))
        input("\nPress Enter to return to menu...")
    elif choice == "q":
        break
    else:
        print("Invalid choice. Try again.")
        clear = False
