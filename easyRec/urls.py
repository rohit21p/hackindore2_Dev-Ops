from django.contrib import admin
from django.urls import path,include
from movies.views import movie_home
urlpatterns = [
    path('',movie_home,name='home'),
    path('admin/', admin.site.urls),
    path('movies/',include('movies.urls')),
    path('accounts/',include('accounts.urls')),
]