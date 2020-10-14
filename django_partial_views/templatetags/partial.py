import re

from django import template

register = template.Library()
nodes = {}


@register.tag("partial")
def partial(parser, token):
    try:
        tag_name, partial_id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            f"{token.contents.split()[0]} tag requires a single argument"
        )
    content = parser.parse(("endpartial",))
    parser.delete_first_token()

    if re.match(r"\"[\w-]+\"", partial_id):
        partial_id = eval(partial_id)

    return PartialNode(partial_id, content)


class PartialNode(template.Node):
    def __init__(self, partial_id, content):
        self.partial_id = partial_id
        self.content = content

    def render(self, context):
        return (
            f'<div data-partial-id="{self.partial_id}">'
            f"  {self.content.render(context)}"
            f"</div>"
        )
