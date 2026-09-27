import time
from core.config import load_settings


def boot_line(text):
    print(f"{text:<32} [OK]")
    time.sleep(0.4)


def boot():
    settings = load_settings()
    nova = settings["nova"]

    print("=" * 70)

    print(r"""
        N   N   OOO   V   V    A
        NN  N  O   O  V   V   A A
        N N N  O   O  V   V  AAAAA
        N  NN  O   O   V V   A   A
        N   N   OOO     V    A   A
""")

    print(f"      {nova['name']} Personal AI Operating System")

    print("=" * 70)
    print()

    boot_line("Loading Configuration")
    boot_line("Initializing Core System")
    boot_line("Loading Command Engine")
    boot_line("Checking Voice Module")
    boot_line("Preparing AI Brain")

    print()

    print("=" * 70)
    print(f"                     {nova['name']} READY")
    print("=" * 70)
