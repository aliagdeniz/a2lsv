"""a2lsv_web URL Configuration

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
from django.urls import include, path
from web_interface.views import web_interface, labeler, manager

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web_interface.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/manager/', manager.ManagerSignUpView.as_view(), name='manager_signup'),
    path('accounts/signup/labeler/', manager.LabelerSignUpView.as_view(), name='labeler_signup'),
]
