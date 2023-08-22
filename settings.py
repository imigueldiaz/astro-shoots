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

    Parameters:
        None

    Returns:
        None
    """
    global ROUTE, STATIC_URL_PATH, SECRET_KEY

    load_dotenv()

    config = configparser.ConfigParser()
    config.read("config.ini")

    ROUTE = config.get("APP", "ROUTE")
    STATIC_URL_PATH = config.get("APP", "STATIC_URL_PATH")
    SECRET_KEY = os.environ.get("SECRET_KEY")
