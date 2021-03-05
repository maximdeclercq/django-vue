from __future__ import annotations

from django.shortcuts import render
from django.urls import reverse
from django.views.generic import TemplateView

from django_vue import VueComponentMixin


class VueSingleFileComponent(VueComponentMixin, TemplateView):
    def __init__(self, template_name=None):
        super().__init__()
        if template_name:
            self.template_name = template_name

    def get(self, *args, **kwargs):
        template_name = self.kwargs.get("template_name", "") or self.template_name
        if not template_name.endswith(".vue"):
            raise ValueError("Only Vue templates are allowed.")
        return render(self.request, template_name)

    def get_vue_definition(self, request, *args, **kwargs) -> str:
        if not self.template_name.endswith(".vue"):
            raise ValueError("Only Vue templates are allowed.")
        kwargs = {"template_name": self.template_name}
        url = reverse("django_vue:components", kwargs=kwargs)
        return f"const {self.get_vue_id()} = httpVueLoader({url});"
