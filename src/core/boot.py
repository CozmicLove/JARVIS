import time
from core.config import load_settings


def boot_line(text):
    print(f"{text:<32} [OK]")
    time.sleep(0.4)


def boot():

    settings = load_settings()
    jarvis = settings["jarvis"]

    print("=" * 70)

    print(r"""
       ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗
       ██║██╔══██╗██╔══██╗██║   ██║██║██╔════╝
       ██║███████║██████╔╝██║   ██║██║███████╗
  ██   ██║██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║
  ╚█████╔╝██║  ██║██║  ██║ ╚████╔╝ ██║███████║
   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝
""")

    print(f"      {jarvis['name']} Personal AI Operating System")

    print("=" * 70)
    print()

    boot_line("Loading Configuration")
    boot_line("Initializing Core System")
    boot_line("Loading Command Engine")
    boot_line("Checking Voice Module")
    boot_line("Preparing AI Brain")

    print()

    print("=" * 70)
    print(f"                     {jarvis['name']} READY")
    print("=" * 70)