from django.urls import path
from . import views
from . import parent
from . import child

urlpatterns = [

    # interval url de connexion 
    path('users/connexion/', views.LoginViews.as_view(), name='user-login'),
    # fin interval url de connexion 


    # debut interval des urls qui conserne user
    path('users/', views.UserApiViews.as_view(), name='user-list-create'),
    path('testesendsms/', views.TestSendSMS.as_view(), name='testesendsms'),
    # fin intervale des url qui conserne le user 

    # debut des routes qui concerne le parent 
    path('parents/', parent.parentRegister.as_view(), name='parentRegister'),
    path('parent/confirm_otp/', parent.ConfirmRegistration.as_view(), name='ConfirmRegistration'),
    # fin des routes qui concerne le parent

    # debut des routes pour l'enfant 
    path('childs/', child.ChildRegister.as_view(), name='ConfirmRegistration'),
    # fin des routes qui conserne l'enfant 

    # les url sur le model qui link le parent au child
    path('lislinkchildtoparent/', views.lislinkchildtoparent.as_view(), name='lislinkchildtoparent'),
    path('qr-code/<int:pk>/', views.GetQRCode.as_view(), name='get_qr_code'),




]