from __future__ import annotations

import json
import re
from collections import OrderedDict
from typing import List, Dict

from bs4 import BeautifulSoup
from django.http import HttpRequest
from django.template.loader import select_template
from django.templatetags.static import static
from django.views.generic import TemplateView
from inflection import camelize, dasherize


class DjangoVueView(TemplateView):
    """A mixin that customizes rendering of a view to annotate children of blocks with
    it's name and to return a JSON with only the blocks if an AJAX request is made."""

    vue_components: Dict[str, DjangoVueComponent] = {}
    vue_data: Dict[str, any] = {}
    vue_routes: OrderedDict[str, DjangoVueView] = OrderedDict()

    def get_vue_name(self):
        return camelize(
            re.sub(r"(component|view)$", "", self.__class__.__name__, re.IGNORECASE)
        )

    def get_vue_definition(self, request, template=None, *args, **kwargs) -> str:
        return f"""
            const {self.get_vue_name()} = {{
              data() {{
                return {json.dumps(self.get_vue_data())}
              }},
              template: `{template or self.get_vue_template(request)}`,
              delimiters: ["[[", "]]"],
            }}
        """

    def get_vue_components(self):
        return self.vue_components

    def get_vue_data(self):
        return self.vue_data

    def get_vue_routes(self):
        return self.vue_routes

    def get_vue_template(self, request, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response.render()
        return response.content.decode("utf-8")

    def get(self, request: HttpRequest, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.render()
        soup = BeautifulSoup(response.content, "lxml")

        head = soup.find("head")

        def script_present(name) -> bool:
            return len(soup.find_all("script", src=lambda x: x and name in x)) > 0

        # Add the required vue library to the head if it is not present
        if not script_present("vue"):
            head.append(
                soup.new_tag("script", attrs={"src": "https://unpkg.com/vue@next"})
            )

        # Add the required vue library to the head if it is not present
        if not script_present("vue-router"):
            head.append(
                soup.new_tag(
                    "script",
                    attrs={"src": "https://unpkg.com/vue-router@next"},
                )
            )

        # Add the required vue-http-loader library to the head if it is not present
        if not script_present("vue3-sfc-loader"):
            head.append(
                soup.new_tag(
                    "script",
                    attrs={
                        "src": (
                            "https://cdn.jsdelivr.net/npm/vue3-sfc-loader@latest"
                            "/dist/vue3-sfc-loader.js"
                        )
                    },
                )
            )

        # Add the required axios library to the head if it is not present
        if not script_present("axios"):
            head.append(
                soup.new_tag(
                    "script", attrs={"src": "https://unpkg.com/axios/dist/axios.min.js"}
                )
            )

        # Add the django-fluid library to the head if it is not present
        if not script_present("django-fluid"):
            head.append(
                soup.new_tag(
                    "script",
                    attrs={
                        "src": static("django-fluid.js"),
                    },
                )
            )

        # Extract styles and scripts from body
        body = soup.find("body")
        styles = [e.extract() for e in body.find_all("style")]
        scripts = [e.extract() for e in body.find_all("script")]
        body_content = body.renderContents().decode("utf-8")

        # Construct Vue app
        vue = soup.new_tag("script")
        definitions = "\n".join(
            [
                c.get_vue_definition(request)
                for c in list(self.get_vue_components().values())
                + list(self.get_vue_routes().values())
            ]
            + [self.get_vue_definition(request, body_content, *args, **kwargs)]
        )
        components = "\n".join(
            f'app.component("{k}", {v.get_vue_name()})'
            for k, v in self.get_vue_components().items()
        )
        routes = ",".join(
            f'{{ path: "{k}", component: {v.get_vue_name()} }}'
            for k, v in self.get_vue_routes().items()
        )
        vue.string = f"""
            {definitions}
            const app = Vue.createApp({self.get_vue_name()})
            {components}
            const router = VueRouter.createRouter({{
              history: VueRouter.createWebHashHistory(),
              routes: [{routes}]
            }})
            app.use(router)
            app.mount("#app")
        """

        # Construct new body
        body.clear()
        body.extend(styles)
        body.append(soup.new_tag("div", id="app"))
        body.append(vue)
        body.extend(scripts)

        response.content = soup.renderContents().decode("utf-8")
        return response


class DjangoVueComponent(DjangoVueView):
    pass


class NativeVueComponent(DjangoVueComponent):
    def get_vue_definition(self, request, *args, **kwargs) -> str:
        return f"""
            const {self.get_vue_name()} = Vue.defineAsyncComponent(() => window["vue3-sfc-loader"].loadModule({select_template(self.get_template_names())}))
        """
