import functools


def fluid_action(function):
    function.is_fluid_action = True

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper
