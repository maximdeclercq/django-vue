# Django Vue

A promising attempt to bring the power of VueJS to native Django.
Write VueJS code and use VueJS Components inside Django templates without extensive code changes! 

## Installation

Install the `django_vue` package
```shell
pip install git+https://github.com/maximdeclercq/django-vue
```

Add `django_vue` to your `INSTALLED_APPS`
```python
INSTALLED_APPS = (
    # ...,
    'django_vue',
)
```

## Usage

```python
from django_vue import DjangoVueComponent
# To be implemented
from django_vue.decorators import VueMethod

class CounterComponent(DjangoVueComponent):
    template_name = "components/counter.html"

    vue_props = ["count"]

    # To be implemented
    @VueMethod
    def inc_counter(self):
        self.vue_data["count"] += 1

class Home(DjangoVueComponent):
    template_name = "home.html"

    vue_components = {
        'counter': CounterComponent(),
    }

    vue_data = {'count': 0}
```
