from django.urls import path
from . import views
from . import parent
from . import child
from django.urls import re_path




urlpatterns = [

    # interval url de connexion 
    path('users/connexion/', views.LoginViews.as_view(), name='user-login'),
    path('phone_login/', views.PhoneLoginView.as_view(), name='phone_login'),
    path('listeAlert/', views.listeAlert.as_view(), name='listeAlert'),


    # fin interval url de connexion 


    # debut interval des urls qui conserne user
    path('users/', views.UserApiViews.as_view(), name='user-list-create'), 
    path('testesendsms/', views.TestSendSMS.as_view(), name='testesendsms'),
    path('otp_password_user/', views.SendOtpUserChangePassword.as_view(), name='otp_password_user'),
    path('confirm__otp_password_user/', views.ConfirmOtpUserForPassword.as_view(), name='confirm_otp_password_user'),
    path('change_password/', views.ChangePasswordUser.as_view(), name='ChangePasswordUser'),
    path('sendB_back_otp/', views.sendBackOtp.as_view(), name='sendBackOtp'),
    # fin intervale des url qui conserne le user 

    # debut des routes qui concerne le parent 
    path('parents/', parent.parentRegister.as_view(), name='parentRegister'),
    path('parent/confirm_otp/', parent.ConfirmRegistration.as_view(), name='ConfirmRegistration'),
    path('parent_update/<slug:slug>/', parent.UpdateParent.as_view(), name='update_parent'),
    path('parent_status/', parent.CounteUserActifAndUserInactif.as_view(), name='parent_status'),
    path('liste_user_actif_inactif/', parent.ListeUserActifInactif.as_view(), name='liste_user_actif_inactif'),
    path('parent_dashbord/<slug:slug>/', parent.ParentDashbord.as_view(), name='parent_dashbord'),
    path('emergency_contact/<slug:slug>/', parent.ParentAddEmergencyContactForChildAlert.as_view(), name='emergency_contact'),
    path('send_alert_for_child/<slug:slug>/', parent.SendAlertAllEmergenctContactForParentToChild.as_view(), name='send_alert_for_child'),
    # fin des routes qui concerne le parent

    # debut des routes pour l'enfant  
    path('childs/', child.RegisterChild.as_view(), name='ConfirmRegistration'),
    path('parent_child_link/', child.ParendChildLink.as_view(), name='parent_child_link'),
    path('child/confirm_otp/', child.ConfirmRegistrationChild.as_view(), name='ConfirmRegistration'),
    path('child/<slug:slug>/', child.childDashbord.as_view(), name='child_dashboard'),
    path('child_location/', child.AddLocalization.as_view(), name='child_location'),
    path('position/<slug:slug>/', child.LastPosition.as_view(), name='child_last_position'),
    path('daily_trajectory/<slug:slug>/', child.DailyTrajectoryView.as_view(), name='daily-trajectory'),
    path('child_update/<slug:slug>/', child.UpdateChild.as_view(), name='update_child'), 
    path('add_allergy/', child.ChildAlergyApiViews.as_view(), name='child_add_allergy'),
    # fin des routes qui conserne l'enfant

    # les url sur le model qui link le parent au child
    path('lislinkchildtoparent/', views.lislinkchildtoparent.as_view(), name='lislinkchildtoparent'),
    path('qr-code/<int:pk>/', views.GetQRCode.as_view(), name='get_qr_code'),
]