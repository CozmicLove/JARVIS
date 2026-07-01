from datetime import datetime


def run():
    now = datetime.now()
    return now.strftime("Current time is %H:%M:%S")