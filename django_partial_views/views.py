from pprint import pprint

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.template.backends.django import reraise
from django.template.context import make_context
from django.template.loader import select_template

from django_partial_views.utils import get_fragments


class PartialMixin:
    """A mixin that returns a JSON with id's and their contents for partial parts of
    the template to replace them."""

    def get(self, request, template_name=None, *args, **kwargs):
        template_name = (
            [template_name] if template_name else []
        ) + self.get_template_names()
        context = self.get_context_data()

        # Return normal response if the request wasn't made with AJAX
        if not request.is_ajax():
            return render(request, template_name, context)

        t = select_template(template_name)
        template, backend = t.template, t.backend
        context = make_context(context, request, autoescape=backend.engine.autoescape)
        return JsonResponse(get_fragments(request, template, context))


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
