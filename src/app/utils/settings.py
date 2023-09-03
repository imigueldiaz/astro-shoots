# settings.py
import configparser
import os

from dotenv import load_dotenv

ROUTE = None
STATIC_URL_PATH = None
SECRET_KEY = None
DEBUG = True


def load_config():
    """
    Loads the configuration settings from the "config.ini" file and environment variables.

    Returns:
        None
    """
    global ROUTE, STATIC_URL_PATH, SECRET_KEY, DEBUG

    load_dotenv()

    config = configparser.ConfigParser()
    config_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "config.ini"
    )
    config.read(config_path)

    ROUTE = config.get("APP", "route")
    STATIC_URL_PATH = config.get("APP", "STATIC_URL_PATH")
    SECRET_KEY = os.environ.get("SECRET_KEY")

    return {
        "route": ROUTE,
        "SECRET_KEY": SECRET_KEY,
        "STATIC_URL_PATH": STATIC_URL_PATH,
        "DEBUG": DEBUG,
    }
