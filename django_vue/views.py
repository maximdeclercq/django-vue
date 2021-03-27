from __future__ import annotations

from django.views.generic import TemplateView

from django_vue import VueComponentMixin


class VueSingleFileComponent(VueComponentMixin, TemplateView):
    def __init__(self, template_name: str = None):
        super().__init__()
        if template_name:
            self.template_name = template_name

    def get_vue_definition(self, request, *args, **kwargs) -> str:
        return f"""
            const {self.get_vue_id()} = window["vue2-sfc-loader"].loadModule("{self.get_vue_id()}.vue", {{
              moduleCache: {{
                vue: Vue,
              }},
              getFile(url) {{
                return Promise.resolve(`{self.get_vue_template(request)}`)
              }},
              addStyle(src) {{
                const style = document.createElement('style');
                style.textContent = src;
                const ref = document.head.getElementsByTagName('style')[0] || null;
                document.head.insertBefore(style, ref);
              }},
            }});
        """

    def get_vue_template(self, request, **kwargs):
        soup = self._get_vue_template_soup(request, **kwargs)
        return self._render_vue_template_soup(soup)
