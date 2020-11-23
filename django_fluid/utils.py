from urllib.parse import urlparse

from bs4 import BeautifulSoup
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.template import Context, NodeList
from django.template.base import TextNode
from django.template.loader_tags import (
    ExtendsNode,
    BlockNode,
    BLOCK_CONTEXT_KEY,
    BlockContext,
)
from django.templatetags.static import static
from django.urls import resolve, translate_url, Resolver404
from django.utils import translation
from django.utils.safestring import mark_safe


def render_to_response(request: HttpRequest, context: Context, nodelist: NodeList):
    """Renders a nodelist and returns it with annotated block tags.

    Only renders the blocks and returns them as a JSON if is_ajax is True.
    """
    extends = next(iter(nodelist.get_nodes_by_type(ExtendsNode)), None)
    blocks = {n.name: n for n in nodelist.get_nodes_by_type(BlockNode)}

    # Render if there is no extends tag
    if not extends:
        return __render_to_response(request, context, nodelist)

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
        return render_to_response(request, context, compiled_parent.nodelist)


def __render_to_response(request: HttpRequest, context: Context, nodelist: NodeList):
    """Helper function that renders a nodelist and returns it with annotated block tags
    assuming there is no extends tag.

    Only renders the blocks and returns them as a JSON if the request was made with AJAX.
    """
    blocks = {}

    def __prerender_blocks(parent_nodelist):
        """Prerender blocks with annotated HTML elements."""
        for i, node in enumerate(parent_nodelist):
            # Prerender block
            if isinstance(node, BlockNode):
                # Wrap block in fluid-block tag
                blocks[node.name] = (
                    f'<fluid-block name="{node.name}">'
                    f"    {node.render(context)}"
                    f"</fluid-block>"
                )
                parent_nodelist[i] = TextNode(mark_safe(blocks[node.name]))

            # Recurse into child nodelists
            for attr in node.child_nodelists:
                child_nodelist = getattr(node, attr, None)
                if child_nodelist:
                    __prerender_blocks(child_nodelist)

    __prerender_blocks(nodelist)

    # Return a JSON of rendered blocks if the request was made with AJAX
    if request.is_ajax():
        return JsonResponse(blocks)

    content = nodelist.render(context)

    soup = BeautifulSoup(content, "lxml")
    head = soup.find("head")

    def script_present(name) -> bool:
        return len(soup.find_all("script", src=lambda x: x and name in x)) > 0

    # Add the required jquery.form library to the head if it is not present
    if not script_present("jquery.form"):
        head.append(
            soup.new_tag(
                "script",
                attrs={
                    "src": (
                        "https://cdnjs.cloudflare.com"
                        "/ajax/libs/jquery.form/4.2.2/jquery.form.min.js"
                    ),
                    "integrity": "sha256-2Pjr1OlpZMY6qesJM68t2v39t+lMLvxwpa8QlRjJroA=",
                    "crossorigin": "anonymous",
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

    # Add the correct tags to links and forms
    for tag in soup.find_all(["a", "form"]):
        sub_path = tag.get("action", "") or tag.get("href", "")
        path = urlparse(request.build_absolute_uri(sub_path)).path
        if path == request.path:
            tag["data-fluid"] = "same"

        # Activate the language the url refers to
        language = translation.get_language_from_path(path)
        if not language:
            language = settings.LANGUAGE_CODE
        translation.activate(language)

        try:
            # Resolve the url
            match = resolve(path)
        except Resolver404:
            # Do nothing if the url does not resolve
            pass
        else:
            # Check if the view the url resolved to is fluid
            view_class = getattr(match.func, "view_class", False)
            is_fluid = view_class and getattr(view_class, "is_fluid", False)
            # TODO: Actually check if the view derives
            if is_fluid:
                tag["data-fluid"] = "derived"

    # Restore the language the request was made in
    translation.activate(request.LANGUAGE_CODE)

    return HttpResponse(soup.renderContents().decode("utf-8"))