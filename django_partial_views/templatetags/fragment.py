from __future__ import annotations

import re

from django import template
from django.template import TemplateSyntaxError
from django.template.loader_tags import (
    BLOCK_CONTEXT_KEY,
    BlockNode,
)
from django.utils.safestring import mark_safe
from lxml import etree

register = template.Library()


class FragmentNode(BlockNode):
    def __init__(self, name, nodelist, parent=None):
        super().__init__(name, nodelist, parent)
        print(name, nodelist, parent)

    def __repr__(self):
        return "<Fragment Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        fragment_context = context.render_context.get(BLOCK_CONTEXT_KEY)
        print(fragment_context)
        with context.push():
            if fragment_context is None:
                context["fragment"] = self
                result = self.nodelist.render(context)
            else:
                push = fragment = fragment_context.pop(self.name)
                print(push.__dict__)
                print(fragment.__dict__)
                if fragment is None:
                    fragment = self
                # Check if the child is also a fragment to prevent inconsistencies
                if not isinstance(fragment, FragmentNode):
                    raise TemplateSyntaxError(
                        f"fragment '{self.name}' is overriden by a block tag. "
                        f"Did you mean to use a fragment tag?"
                    )
                # Create new fragment so we can store context without thread-safety
                # issues.
                fragment = type(self)(fragment.name, fragment.nodelist)
                fragment.context = context
                context["fragment"] = fragment
                print(context)
                result = fragment.nodelist.render(context)
                if push is not None:
                    fragment_context.push(self.name, push)
        # Wrap the contents in a root element for xml modification
        root = etree.fromstring(f"<root>{result}</root>")
        for element in root:
            element.attrib["data-fragment-name"] = self.name
        # Remove the root element and mark it safe
        return mark_safe(re.sub(r"(^<root>|</root>$)", "", etree.tounicode(root)))

    def super(self):
        if not hasattr(self, "context"):
            raise TemplateSyntaxError(
                "'%s' object has no attribute 'context'. Did you use "
                "{{ fragment.super }} in a base template?" % self.__class__.__name__
            )
        return super().super()


@register.tag("fragment")
def do_fragment(parser, token):
    """Define a fragment that can be overridden by child templates and be rendered
    separately to be rendered after an ajax call."""
    # token.split_contents() isn't useful here because this tag doesn't accept variable as arguments
    bits = token.contents.split()
    if len(bits) != 2:
        raise TemplateSyntaxError("'%s' tag takes only one argument" % bits[0])
    fragment_name = bits[1]
    # Keep track of the names of FragmentNodes found in this template, so we can
    # check for duplication.
    try:
        if fragment_name in parser.__loaded_blocks:
            raise TemplateSyntaxError(
                "'%s' tag with name '%s' appears more than once"
                % (bits[0], fragment_name)
            )
        parser.__loaded_blocks.append(fragment_name)
    except AttributeError:  # parser.__loaded_blocks isn't a list yet
        parser.__loaded_blocks = [fragment_name]
    nodelist = parser.parse(("endfragment",))

    # This check is kept for backwards-compatibility. See #3100.
    endfragment = parser.next_token()
    acceptable_endfragments = ("endfragment", "endfragment %s" % fragment_name)
    if endfragment.contents not in acceptable_endfragments:
        parser.invalid_block_tag(endfragment, "endfragment", acceptable_endfragments)

    return FragmentNode(fragment_name, nodelist)
