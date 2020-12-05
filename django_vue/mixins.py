from __future__ import annotations

import json
import re
from collections import OrderedDict
from typing import Dict, List, Type

from bs4 import BeautifulSoup
from django.http import HttpRequest

from .plugins import VuePlugin


class DjangoVueComponentMixin:
    """A mixin that customizes rendering of a view to annotate children of blocks with
    it's name and to return a JSON with only the blocks if an AJAX request is made."""

    vue_components: Dict[str, any] = {}
    vue_data: Dict[str, any] = {}
    vue_emits: List[str] = []
    vue_is_root: bool = False
    vue_plugins: List[Type[VuePlugin]] = []
    vue_props: List[str] = []
    vue_routes: OrderedDict[str, any] = OrderedDict()

    def get_vue_name(self):
        return f"c{id(self)}"

    def get_vue_definition(self, request, template=None, *args, **kwargs) -> str:
        components = ",".join(
            f'"{k}":{v.get_vue_name()}' for k, v in self.get_vue_components().items()
        )
        return self.__clear_indentation(
            f"""const {self.get_vue_name()} = {{
                components: {{{components}}},
                data() {{
                  return {json.dumps(self.get_vue_data())}
                }},
                emits: {json.dumps(self.get_vue_emits())},
                props: {json.dumps(self.get_vue_props())},
                template: `{template or self.get_vue_template(request)}`,
              }}"""
        )

    def get_vue_components(self):
        return self.vue_components

    def get_vue_data(self):
        return self.vue_data

    def get_vue_emits(self):
        return self.vue_emits

    def get_vue_plugins(self):
        return self.vue_plugins

    def get_vue_props(self):
        return self.vue_props

    def get_vue_routes(self):
        return self.vue_routes

    def get_vue_template(self, request, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response.render()
        soup = BeautifulSoup(response.content, "html5lib")

        body = soup.find("body")

        # TODO: What to do with styles and scripts from other views?
        _styles = [e.extract() for e in body.find_all("style")]
        _scripts = [e.extract() for e in body.find_all("script")]

        template = body.renderContents().decode("utf-8")

        # Replace brackets with curly braces so we don't have to override this in Vue
        return template.replace("[[", "{{").replace("]]", "}}")

    def get(self, request: HttpRequest, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Only modify rendering for the root component
        if not self.vue_is_root:
            return response

        response.render()
        soup = BeautifulSoup(response.content, "html5lib")

        head = soup.find("head")

        def search_name(name: str, text: str):
            return text and re.search(f"\b{name.lower()}\b", text.lower()) is not None

        def add_script_if_not_present(name: str, src: str) -> None:
            if any(soup.find_all("script", src=lambda t: search_name(name, t))):
                head.append(soup.new_tag("script", attrs={"src": src}))

        def add_style_if_not_present(name: str, href: str) -> None:
            if any(soup.find_all("link", href=lambda t: search_name(name, t))):
                attrs = {"type": "text/css", "rel": "stylesheet", "href": href}
                head.append(soup.new_tag("link", attrs=attrs))

        # Add the required libraries to the head if they are not present
        add_script_if_not_present("axios", "https://unpkg.com/axios")
        add_script_if_not_present("vue", "https://unpkg.com/vue@latest")
        add_script_if_not_present("vue-router", "https://unpkg.com/vue-router@latest")
        add_script_if_not_present(
            "http-vue-loader", "https://unpkg.com/http-vue-loader"
        )

        # Add the libraries from the plugin
        for plugin in self.vue_plugins:
            for name, src in plugin.get_vue_script_sources().items():
                add_script_if_not_present(name, src)
            for name, href in plugin.get_vue_style_sources().items():
                add_style_if_not_present(name, href)

        # Extract styles and scripts from body
        body = soup.find("body")
        styles = [e.extract() for e in body.find_all("style")]
        scripts = [e.extract() for e in body.find_all("script")]
        body.clear()

        # Construct Vue app
        vue = soup.new_tag("script")
        # Get unique component instances by their name
        instances = {
            c.get_vue_name(): c
            for c in list(self.get_vue_components().values())
            + list(self.get_vue_routes().values())
            + [self]
        }.values()
        definitions = "\n".join([c.get_vue_definition(request) for c in instances])
        routes = ",".join(
            f'{{ path: "{k}", component: {v.get_vue_name()} }}'
            for k, v in self.get_vue_routes().items()
        )
        vue.string = self.__clear_indentation(
            f"""{definitions}
                const router = VueRouter({{ routes: [{routes}] }})
                {self.get_vue_name()}.el = "#app"
                {self.get_vue_name()}.router = router
                new Vue({self.get_vue_name()}).$mount("#app")"""
        )

        # Construct new body
        body.extend(styles)
        body.append(soup.new_tag("div", id="app"))
        body.append(vue)
        body.extend(scripts)

        response.content = soup.renderContents().decode("utf-8")
        return response

    @staticmethod
    def __clear_indentation(s: str) -> str:
        return re.sub(r"\n\s*", "", s, re.IGNORECASE)
