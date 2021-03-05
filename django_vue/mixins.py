from __future__ import annotations

import json
import re

from bs4 import BeautifulSoup
from django.http import HttpRequest
from django.urls.resolvers import URLPattern
from inflection import dasherize
from typing import Dict, List, Type

from .plugins import VuePlugin


class VueComponentMixin:
    """A mixin that customizes rendering of a view to annotate children of blocks with
    it's name and to return a JSON with only the blocks if an AJAX request is made."""

    vue_components: List[any] = []
    vue_data: Dict[str, any] = {}
    vue_emits: List[str] = []
    vue_plugins: List[Type[VuePlugin]] = []
    vue_props: List[str] = []
    vue_routes: List[URLPattern] = []

    _vue_is_root: bool = False

    def __hash__(self):
        return hash(type(self).__name__)

    def get_vue_id(self):
        return f"c{hash(self)}"

    def get_vue_name(self):
        # Strip last part of class name
        return dasherize(type(self).__name__).rsplit("-", 1)[0]

    def get_vue_definition(self, request, template=None, *args, **kwargs) -> str:
        # Get instances of components
        vue_components = [
            v.view_class(**v.view_initkwargs) for v in self.get_vue_components()
        ]
        components = ",".join(
            f'"{c.get_vue_name()}":{c.get_vue_id()}' for c in vue_components
        )
        return f"""
            const {self.get_vue_id()} = {{
              components: {{{components}}},
              data() {{
                return {json.dumps(self.get_vue_data())};
              }},
              emits: {json.dumps(self.get_vue_emits())},
              props: {json.dumps(self.get_vue_props())},
              template: `{self.get_vue_template(request)}`
            }};
        """

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
        soup = self._get_vue_template_soup(request, **kwargs)
        # Extract body from soup
        body = soup.find("body")

        return self._render_vue_template_soup(body)

    def dispatch(self, request, *args, **kwargs):
        if not self._vue_is_root:
            raise RuntimeError(
                "This Vue component is not supposed to be used as a Django view."
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request: HttpRequest, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        # Only modify rendering for the root component
        if not self._vue_is_root:
            return response

        response.render()
        soup = BeautifulSoup(response.content, "html5lib")

        head = soup.find("head")

        def search_name(name: str, text: str):
            return text and re.search(f"\b{name.lower()}\b", text.lower()) is not None

        def add_script_if_not_present(name: str, src: str) -> None:
            if not any(soup.find_all("script", src=lambda t: search_name(name, t))):
                head.append(soup.new_tag("script", attrs={"src": src}))

        def add_style_if_not_present(name: str, href: str) -> None:
            if not any(soup.find_all("link", href=lambda t: search_name(name, t))):
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

        body = soup.find("body")
        body.clear()

        # Construct Vue app
        vue = soup.new_tag("script")
        # Get instances of components
        vue_components = [
            v.view_class(**v.view_initkwargs) for v in self.get_vue_components()
        ]
        vue_routes = {
            r.pattern: r.callback.view_class(**r.callback.view_initkwargs)
            for r in self.get_vue_routes()
        }
        # Get unique component instances by their name
        components = vue_components + list(vue_routes.values()) + [self]
        instances = {c.get_vue_id(): c for c in components}.values()
        definitions = "\n".join([c.get_vue_definition(request) for c in instances])
        routes = ",".join(
            f'{{ path: "{r}", component: {c.get_vue_id()}}}'
            for r, c in vue_routes.items()
        )
        vue.string = f"""
            {definitions}
            const router = new VueRouter({{ routes: [{routes}] }});
            {self.get_vue_id()}.el = "#app";
            {self.get_vue_id()}.router = router;
            new Vue({self.get_vue_id()});
        """

        # Construct new body
        body.append(soup.new_tag("div", id="app"))
        body.append(vue)

        response.content = self._render_template_soup(soup)
        return response

    def _get_vue_template_soup(self, request, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        response = self.render_to_response(context)
        response.render()
        return BeautifulSoup(response.content, "html5lib")

    @classmethod
    def _render_vue_template_soup(cls, s: BeautifulSoup):
        content = cls._render_template_soup(s)

        # Replace brackets with curly braces so we don't have to override this in Vue
        content = content.replace("[[", "{{").replace("]]", "}}")

        # Escape scripts and styles
        content = (
            content.replace("<script", '<component is="script"')
            .replace("</script>", r"</component>")
            .replace("<style", '<component is="style"')
            .replace("</style>", r"</component>")
            .replace("`", r"\`")
            .replace("${", r"\${")
        )

        return content

    @staticmethod
    def _render_template_soup(s: BeautifulSoup):
        lines = s.encode_contents().decode("utf-8").split("\n")
        return "".join(line.strip() for line in lines)


class VueViewMixin(VueComponentMixin):
    _vue_is_root: bool = True
