"""sippv2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from django.urls import path, re_path, include
from django.views.generic.base import TemplateView
from app01 import views

urlpatterns = [
    path('admin/', admin.site.urls),
    re_path(r'^api-auth/', include('rest_framework.urls')),
    re_path(r'^$', TemplateView.as_view(template_name='index.html')),
    re_path(r'login$', views.Login.as_view()),
    re_path(r'register$', views.Register.as_view()),
    re_path(r'user/$', views.user.as_view()),
    re_path(r'^changePasswd$', views.changePasswd.as_view()),
    re_path(r'WorkBench!(?P<slug>\w+)$', views.WorkBench.as_view()),
    re_path(r'SippScript!(?P<slug>\w+)$', views.SippScript.as_view()),
    re_path(r'Config!(?P<slug>\w+)$', views.Config.as_view()),
    re_path(r'TaskStatus!(?P<slug>\w+)$', views.TaskStatus.as_view()),
    #re_path(r'^SippScriptPathTree$', views.SippScriptPathTree.as_view())
]
