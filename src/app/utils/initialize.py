# initialize.py
import logging

from flask_limiter import Limiter
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect


def init_logging(app):
    """
    Initializes logging for the application.

    Args:
        app (object): The application object.

    Returns:
        None
    """
    handler = logging.FileHandler("app.log")
    handler.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)


def init_limiter(app):
    """
    Initializes a new `Limiter` object with the given Flask `app` instance and sets the default limits for the API.

    Parameters:
        app (Flask): The Flask application instance.

    Returns:
        Limiter: A new `Limiter` object with the default limits set.
    """
    return Limiter(app, default_limits=["10000 per day", "2000 per hour"])


def init_talisman(app):
    """
    Initializes the Talisman middleware for the Flask application.

    Parameters:
        app (Flask): The Flask application instance.

    Returns:
        Talisman: The initialized Talisman middleware instance.
    """
    csp = {
        "default-src": "'self'",
        "img-src": ["*", "data:"],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",  # For Bootstrap, Fork-Awesome and Select2
            "https://code.jquery.com",  # For jQuery
        ],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.jsdelivr.net",  # For Bootstrap, Fork-Awesome and Select2
        ],
        "font-src": ["'self'", "https://cdn.jsdelivr.net"],  # Para Fork-Awesome
    }
    return Talisman(app, content_security_policy=csp)


def init_csrf(app):
    """
    Initializes Cross-Site Request Forgery (CSRF) protection for the given Flask app.

    :param app: The Flask app to initialize CSRF protection for.
    :type app: Flask
    :return: The initialized CSRFProtect object.
    :rtype: CSRFProtect
    """
    return CSRFProtect(app)
