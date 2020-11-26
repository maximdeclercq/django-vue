from __future__ import annotations

import json
from typing import List, Callable

from bs4 import BeautifulSoup
from django.http import HttpRequest
from django.templatetags.static import static
from django.utils.text import slugify
from django.views.generic import TemplateView


class VueView(TemplateView):
    """A mixin that customizes rendering of a view to annotate children of blocks with
    it's name and to return a JSON with only the blocks if an AJAX request is made."""

    vue_components: List[VueComponent] = []
    vue_data: dict = {}

    def get_vue_components(self):
        return self.vue_components

    def get_vue_data(self):
        return self.vue_data

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
                soup.new_tag(
                    "script",
                    attrs={
                        "src": "https://unpkg.com/vue@next",
                    },
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

        body = soup.find("body")
        other_scripts = [e.extract() for e in body.find_all("script")]
        body_content = body.renderContents().decode("utf-8")
        body.clear()

        body.append(soup.new_tag("div", id="app"))

        script = soup.new_tag("script")
        script.string = f"""
            const app = Vue.createApp({{
              data() {{
                return {json.dumps(self.get_vue_data())}
              }},
              template: `{body_content}`,
              delimiters: ["[[", "]]"],
            }})
        """
        for c in self.get_vue_components():
            script.string += f"""
                app.component("{c.get_vue_name()}", {{
                  data() {{
                    return {json.dumps(c.get_vue_data())}
                  }},
                  template: `{c.get_vue_template(request)}`
                }})
            """
        script.string += 'app.mount("#app")'
        body.append(script)
        body.extend(other_scripts)

        response.content = soup.renderContents().decode("utf-8")
        return response


class VueComponent(VueView):
    def get_vue_name(self):
        return slugify(self.__class__.__name__)

    def get_vue_template(self, request, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response.render()
        return response.content
