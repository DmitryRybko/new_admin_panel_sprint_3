from django.urls import path
from . import views

urlpatterns = [
    path('movies/', views.MoviesListApi.as_view()),
    path('movies/<uuid:movie_id>/', views.MoviesDetailApi.as_view()),
]

