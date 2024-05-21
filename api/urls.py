from django.urls import path
from . import views
from . import parent
from . import child
from django.urls import re_path


urlpatterns = [

    # interval url de connexion 
    path('users/connexion/', views.LoginViews.as_view(), name='user-login'),
    path('phone_login/', views.PhoneLoginView.as_view(), name='phone_login'),

    # fin interval url de connexion 


    # debut interval des urls qui conserne user
    path('users/', views.UserApiViews.as_view(), name='user-list-create'), 
    path('testesendsms/', views.TestSendSMS.as_view(), name='testesendsms'),
    path('otp_password_user/', views.SendOtpUserChangePassword.as_view(), name='otp_password_user'),
    path('confirm__otp_password_user/', views.ConfirmOtpUserForPassword.as_view(), name='confirm_otp_password_user'),
    path('change_password/', views.ChangePasswordUser.as_view(), name='ChangePasswordUser'),
    # fin intervale des url qui conserne le user 

    # debut des routes qui concerne le parent 
    path('parents/', parent.parentRegister.as_view(), name='parentRegister'),
    path('parent/confirm_otp/', parent.ConfirmRegistration.as_view(), name='ConfirmRegistration'),
    # fin des routes qui concerne le parent

    # debut des routes pour l'enfant  
    path('childs/', child.RegisterChild.as_view(), name='ConfirmRegistration'),
    path('parent_child_link/', child.ParendChildLink.as_view(), name='parent_child_link'),
    path('child/confirm_otp/', child.ConfirmRegistrationChild.as_view(), name='ConfirmRegistration'),
    path('child/<slug:slug>/', child.childDashbord.as_view(), name='child_dashboard'),


    # fin des routes qui conserne l'enfant 

    # les url sur le model qui link le parent au child
    path('lislinkchildtoparent/', views.lislinkchildtoparent.as_view(), name='lislinkchildtoparent'),
    path('qr-code/<int:pk>/', views.GetQRCode.as_view(), name='get_qr_code'),




]