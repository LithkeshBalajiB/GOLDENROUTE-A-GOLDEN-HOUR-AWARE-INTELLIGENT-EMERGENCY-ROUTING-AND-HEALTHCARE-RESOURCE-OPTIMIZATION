from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [

    path('admin/', admin.site.urls),

    # First page → login page
    path('', views.login_view, name="home"),

    # Other app URLs
    path('', include('core.urls')),

]