from django.template import TemplateDoesNotExist, NodeList
from django.template.backends.django import reraise
from django.template.base import TextNode
from django.template.loader_tags import (
    ExtendsNode,
    BlockNode,
    BLOCK_CONTEXT_KEY,
    BlockContext,
)

from django_partial_views.templatetags.fragment import FragmentNode


def get_fragments(request, template, context):
    """Renders dynamic block tags and returns them."""
    try:
        with context.render_context.push_state(template):
            if context.template is None:
                with context.bind_template(template):
                    context.template_name = template.name
                    return get_fragments_from_nodelist(
                        request, template.nodelist, context
                    )
            return get_fragments_from_nodelist(request, template.nodelist, context)
    except TemplateDoesNotExist as exc:
        reraise(exc, template.backend)


def get_fragments_from_nodelist(request, nodelist: NodeList, context):
    extends_nodes = nodelist.get_nodes_by_type(ExtendsNode)

    blocks = {n.name: n for n in nodelist.get_nodes_by_type(BlockNode)}
    fragments = {n.name: n for n in nodelist.get_nodes_by_type(FragmentNode)}

    # Return rendered fragments if there is no extends tag
    if len(extends_nodes) <= 0:
        return {name: fragment.render(context) for name, fragment in fragments.items()}

    extends = extends_nodes[0]
    compiled_parent = extends.get_parent(context)

    if BLOCK_CONTEXT_KEY not in context.render_context:
        context.render_context[BLOCK_CONTEXT_KEY] = BlockContext()
    block_context = context.render_context[BLOCK_CONTEXT_KEY]

    # Add the block nodes from this node to the block context
    block_context.add_blocks(blocks)

    # If this block's parent doesn't have an extends node it is the root,
    # and its block nodes also need to be added to the block context.
    for node in compiled_parent.nodelist:
        # The ExtendsNode has to be the first non-text node.
        if not isinstance(node, TextNode):
            if not isinstance(node, ExtendsNode):
                blocks = {
                    n.name: n
                    for n in compiled_parent.nodelist.get_nodes_by_type(BlockNode)
                }
                block_context.add_blocks(blocks)
            break

    # Call Template._render explicitly so the parser context stays
    # the same.
    with context.render_context.push_state(compiled_parent, isolated_context=False):
        return get_fragments_from_nodelist(request, compiled_parent.nodelist, context)
