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

This example uses bootstrap for styling. Don't worry it will work just fine without. An easy way to introduce Bootstrap4 into your Templates can be found [here](https://pypi.org/project/django-bootstrap4/).

```python
# views.py

from django_vue import DjangoVueComponent

class CounterComponent(DjangoVueComponent):
    template_name = "components/counter.html"

    vue_data = ["count"]

class Home(DjangoVueComponent):
    template_name = "home.html"

    vue_components = {
        'counter': CounterComponent(),
    }
```

```HTML
<!-- templates/components/counter.html -->
<div class="d-flex justify-content-center">
    <button class="mx-2 btn btn-info" v-on:click="count -= 1">-1</button>
    <h3>[[ count ]]</h3>
    <button class="mx-2 btn btn-info" v-on:click="count += 1">+1</button>
</div>
```
```HTML
<!-- template/home.html -->
<div class="row">
    <div class="alert alert-success" style="margin-top: 30px; width: 100%;">
        <counter></counter>
    </div>
</div>
```
