from django.http import HttpResponse, HttpRequest
from django.template import TemplateDoesNotExist
from django.template.backends.django import reraise
from django.template.context import make_context

from django_fluid.utils import render_to_response


class FluidMixin:
    """A mixin that customizes rendering of a view to annotate children of blocks with
    it's name and to return a JSON with only the blocks if an AJAX request is made."""

    is_fluid = True

    def get(self, request: HttpRequest, *args, **kwargs):
        response = super().get(request)

        template = response.resolve_template(response.template_name)
        context = response.resolve_context(response.context_data)

        return self.__render(template, context, request)

    @staticmethod
    def __render(template, context=None, request=None):
        template, backend = template.template, template.backend
        context = make_context(context, request, autoescape=backend.engine.autoescape)
        try:
            with context.render_context.push_state(template):
                nodelist = template.nodelist
                if context.template is None:
                    with context.bind_template(template):
                        context.template_name = template.name
                        return render_to_response(nodelist, context, request.is_ajax())
                return render_to_response(nodelist, context, request.is_ajax())
        except TemplateDoesNotExist as exc:
            reraise(exc, backend)


class FluidActionMixin(FluidMixin):
    """A mixin class that makes it able to define buttons in templates that execute
    functions and rerender the template.
    """

    def dispatch(self, request, *args, **kwargs):
        """Execute the specified action function and rerender the template."""
        if "action" not in request.POST:
            return super().dispatch(request, *args, **kwargs)

        # Extract the action from the post value and check if it is callable
        action, *params = request.POST["action"].split("|")
        function = getattr(self, action, None)
        if (
            not function
            or not callable(function)
            or not hasattr(function, "is_action")
            or not function.is_action
        ):
            return HttpResponse(
                f"{action}({', '.join(params)}) is not a valid action.", status=400
            )

        # Call the action and continue rendering
        function(request, *params)
        return super().dispatch(request, *args, **kwargs)
