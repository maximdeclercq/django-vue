import functools

from django_partial_views import PartialActionView


class register_action:
    def __init__(self, template_name=None, target_id=None):
        self.template_name = template_name
        self.target_id = target_id

    def __call__(self, function):
        self.function = function

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)

        return wrapper

    def __set_name__(self, owner, name):
        # Replace ourself with the original method
        setattr(owner, name, self.function)

        if not issubclass(owner, PartialActionView):
            return

        # Register action in class registry
        owner.action_registry[name] = self.function
