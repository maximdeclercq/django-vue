import functools


def register_action(template_name=None):
    def decorator(function):
        function.is_action = True
        function.template_name = template_name

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)

        return wrapper

    return decorator
