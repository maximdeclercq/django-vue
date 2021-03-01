from django.urls import re_path

from . import views

app_name = "django_vue"
urlpatterns = [
    re_path(
        "component/(?P<template_name>.*)",
        views.VueSingleFileComponent.as_view(),
        name="component",
    ),
]
