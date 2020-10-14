from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from django.template import loader


class PartialMixin:
    """A mixin that returns a JSON with id's and their contents for partial parts of
    the template to replace them."""

    def get(self, request, template_name=None, *args, **kwargs):
        content = loader.render_to_string(
            template_name or self.get_template_names()[0],
            self.get_context_data(),
            request,
        )
        if request.is_ajax():
            soup = BeautifulSoup(content, "lxml")
            return JsonResponse(
                {
                    item["data-partial-id"]: str(item)
                    for item in soup.find_all()
                    if "data-partial-id" in item.attrs
                }
            )
        return HttpResponse(content)


class ActionMixin(PartialMixin):
    """A mixin class that makes it able to define buttons in templates that execute
    functions and rerender the template.
    """

    def post(self, request, *args, **kwargs):
        """Execute the specified action function and rerender the template."""
        actions = [k for k in request.POST if k.startswith("action|")]
        if not actions:
            return HttpResponse(status=400)

        # Extract the action from the post name and check if it is callable
        _, action, *params = actions[0].split("|")
        if not action or not hasattr(self, action):
            return HttpResponse(status=400)

        function = getattr(self, action)
        if (
            not callable(function)
            and not hasattr(function, "is_action")
            or not function.is_action
        ):
            return HttpResponse(status=400)

        # Call the action
        function(request, *params)

        # Render the original response
        return super().get(request, function.template_name, *args, **kwargs)
