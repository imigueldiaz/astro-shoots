# logger.py

from functools import wraps


def log_exceptions(app):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                app.logger.exception("An error occurred: %s", str(e))
                return (
                    "An error occurred. Please check the logs for more information.",
                    500,
                )

        return wrapped

    return decorator
