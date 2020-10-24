# Django Fluid

A promising attempt to bring the power of single-page applications to Django.
Make your views quick and fluid without any configuration or extensive code changes! 

## Installation

Install the `django_fluid` package
```shell
pip install git+https://github.com/maximdeclercq/django-fluid
```

Add `django_fluid` to your `INSTALLED_APPS`
```python
INSTALLED_APPS = (
    # ...,
    'django_fluid',
)
```

## Usage

To use this library, simply add FluidMixin to you template view and your view will become fluid!

```python
class KittenView(FluidMixin, TemplateView):
    template_name = "kitten.html"
```

## Roadmap

- [ ] Allowing to register custom template tags and nodes (and VariableNode, IfNode and ForNode) to refresh.
- [ ] Wrap every dynamic content inside a custom HTML tag to replace it when refreshing.
- [ ] Do some extensive testing on how stable this extension is.
- [ ] Add documentation about FluidActionMixin.

