import logging
from datetime import datetime
from functools import wraps

from flask import request


def log_exceptions(app):
    """
    Decorator function that logs exceptions that occur within the decorated function.

    Parameters:
    - app: The Flask application object.

    Returns:
    - decorator: The decorator function that logs exceptions and returns an error message if an exception occurs.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    handler = logging.FileHandler("app.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                now = datetime.utcnow()
                logger.exception("An error occurred at %s: %s", now, str(e))

                if request:
                    client_details = {
                        "User-Agent": request.headers.get("User-Agent"),
                        "Remote-Addr": request.remote_addr,
                        # Add more details as needed
                    }
                    logger.info("Client Details: %s", client_details)

                return (
                    "An error occurred. Please check the logs for more information.",
                    500,
                )

        return wrapped

    return decorator
