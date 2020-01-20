"""storage URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from rest_framework.routers import SimpleRouter

from scenario.views import ScenarioView, RoomView, CameraView
from session.views import SessionView, RecordView
from editor.views import get_templates, get_scenario, update_scenario

router = SimpleRouter()
router.register(r'scenario', ScenarioView)
router.register(r'room', RoomView)
router.register(r'camera', CameraView)
router.register(r'session', SessionView)
router.register(r'record', RecordView)

urlpatterns = [
    url('^', include(router.urls)),
    url('^get_templates/$', get_templates),
    url('^get_scenario/$', get_scenario),
    url('^update_scenario/$', update_scenario),
    path('admin/', admin.site.urls),
]
