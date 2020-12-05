from __future__ import annotations

from django.views.generic import TemplateView, ListView, DetailView

from .mixins import DjangoVueComponentMixin


class DjangoVueTemplateView(DjangoVueComponentMixin, TemplateView):
    pass


class DjangoVueListView(DjangoVueComponentMixin, ListView):
    pass


class DjangoVueDetailView(DjangoVueComponentMixin, DetailView):
    pass


class DjangoVueComponent(DjangoVueTemplateView):
    def dispatch(self, request, *args, **kwargs):
        raise RuntimeError(
            "This Vue component is not supposed to be used as a Django View."
        )


class SingleFileVueComponent(DjangoVueComponent):
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
