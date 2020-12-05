from __future__ import annotations

from django.views.generic import TemplateView

from .mixins import VueComponentMixin


class SingleFileVueComponent(VueComponentMixin, TemplateView):
    def __init__(self, template_name=None):
        super().__init__()
        if template_name:
            self.template_name = template_name

    def get_vue_definition(self, request, *args, **kwargs) -> str:
        return f"""
            const {self.get_vue_name()} = Vue.defineAsyncComponent(() => loadModule("{self.get_vue_name()}.vue", {{
              moduleCache: {{
                vue: Vue,
              }},
              getFile(url) {{
                return Promise.resolve(/*<!--*/`{self.get_vue_template(request)}`/*-->*/)
              }},
              addStyle(src) {{
                const style = document.createElement('style');
                style.textContent = src;
                const ref = document.head.getElementsByTagName('style')[0] || null;
                document.head.insertBefore(style, ref);
              }},
            }}))
        """

    def get_vue_template(self, request, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response.render()

        template = response.content.decode("utf-8")

        # Replace brackets with curly braces so we don't have to override this in Vue
        return template.replace("[[", "{{").replace("]]", "}}")
