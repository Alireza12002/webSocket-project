from django.urls import path, include
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.index),
    path('game/<str:room>/',views.gameroom)

]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]