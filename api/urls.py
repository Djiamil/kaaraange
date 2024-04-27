from django.urls import path
from . import views

urlpatterns = [
    # interval url de connexion 
    path('users/connexion/', views.LoginViews.as_view(), name='user-login'),
    # fin interval url de connexion 


    # debut interval des urls qui conserne user
    path('users/', views.UserApiViews.as_view(), name='user-list-create'),
    # fin intervale des url qui conserne le user
]