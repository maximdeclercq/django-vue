from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from django.views.generic import TemplateView


class PartialView(TemplateView):
    def get_template_names(self):
        template_names = super().get_template_names()
        if not self.request.is_ajax():
            return template_names
        return ["/_".join(name.rsplit("/", 1)) for name in template_names]


class PartialActionView(PartialView):
    action_registry = {}

    def get(self, request, *args, **kwargs):
        template_name = self.get_template_names()[0]
        content = loader.render_to_string(
            template_name, self.get_context_data(), request
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

    def post(self, request, *args, **kwargs):
        if not request.is_ajax():
            return HttpResponse(status=400)

        _, action, *params = next(
            (k for k in request.POST if k.startswith("action|")), "|"
        ).split("|")
        template_name = self.get_template_names()[0]
        if action:
            function = f"_{action}"
            if hasattr(self, function) and callable(getattr(self, function)):
                getattr(self, function)(request, *params)
                return render(request, template_name, self.get_context_data())
            return HttpResponse(status=400)
        return super().get(request, *args, **kwargs)
