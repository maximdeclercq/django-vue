from bs4 import BeautifulSoup
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.templatetags.static import static
from django.views.generic import TemplateView


class VueView(TemplateView):
    """A mixin that customizes rendering of a view to annotate children of blocks with
    it's name and to return a JSON with only the blocks if an AJAX request is made."""

    components = []
    data = {}

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if not isinstance(response, TemplateResponse):
            return response

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
            const {{ createApp }} = Vue

            const App = {{
              data() {{
                return {{
                  name: "Gregg",
                }}
              }},
              template: `{body_content}`,
              delimiters: ["[[", "]]"],
            }}
            createApp(App).mount("#app")
        """
        body.append(script)
        body.extend(other_scripts)

        response.content = soup.renderContents().decode("utf-8")
        return response


class VueComponentView(VueView):
    pass
