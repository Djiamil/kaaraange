from django.urls import path
from . import views
from . import parent
from . import child
from . import divice
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
    path('send_notification/<slug:slug>/', views.sendNotificationOnly.as_view(), name='send_notification_only'),
    path('delete_user/', views.DeleteUserView.as_view(), name='user_delete'),
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
    path('notification_liste/<slug:slug>/', parent.ParentNotificationListe.as_view(), name='notification_parent_liste'),
    path('addPointTrajetForChild/', parent.addPointTrajetForChild.as_view(), name='addPointTrajetForChild'),
    path('addPerimetreDeSecurityForChild/', parent.addPerimetreDeSecurityForChild.as_view(), name='addPerimetreDeSecurityForChild'),
    path('perimetre_ecurite/<slug:slug>/', parent.PerimetreSecuriteView.as_view(), name='get_delete_or_update_perimetre_securité'),
    path('point_trajet/<slug:slug>/', parent.PointDeReferenceViews.as_view(), name='get_delete_or_update_point_trajet'),
    path('traitement_demande/', parent.ParentAcceptedOrDismissRequest.as_view(), name='traitement_demande'),
    path('detail_emande/<slug:slug>/', parent.DetailDemandeForNotification.as_view(), name='detail_emande'),
    path('perimetreSecure_state/<slug:slug>/', parent.AnabledOrDisabledPerimetreDesecurite.as_view(), name='anabled_or_disabled_perimetre_desecurite'),
    path('child_liste/<slug:slug>/', parent.GetAllChildForthisParent.as_view(), name='all_child_liste_for_parent'),
    path('perimetre_create/', parent.ParentAddPerimetreOfSecurity.as_view(), name='perimetre_create'),
    path('child_safety_perimetre/', parent.ConnectChildSafetyPerimeter.as_view(), name='child_safety_perimetre'),
    path('parent/<slug:slug>/perimetres/', parent.ParentPerimetreListView.as_view(), name='parent-perimetres'),
    path('child/<slug:slug>/perimetres/', parent.ChildPerimetreListView.as_view(), name='child-perimetres'),

    # fin des routes qui concerne le parent  

    # debut des routes pour l'enfant  
    path('childs/', child.RegisterChild.as_view(), name='ConfirmRegistration'),
    path('parent_child_link/', child.ParendChildLink.as_view(), name='parent_child_link'),
    path('child/confirm_otp/', child.ConfirmRegistrationChild.as_view(), name='ConfirmRegistration'),
    path('child/<slug:slug>/', child.childDashbord.as_view(), name='child_dashboard'),
    path('child_location/', child.AddLocalization.as_view(), name='child_location'),
    path('position/<slug:slug>/', child.LastPosition.as_view(), name='child_last_position'),
    # path('daily_trajectory/<slug:slug>/<str:type>/', child.DailyTrajectoryView.as_view(), name='daily-trajectory'),
    path('daily_trajectory/<slug:slug>/', child.DailyTrajectoryView.as_view(), name='daily-trajectory-default'),
    path('daily_trajectory/<slug:slug>/<str:type>/', child.DailyTrajectoryView.as_view(), name='daily-trajectory'),
    path('child_update/<slug:slug>/', child.UpdateChild.as_view(), name='update_child'), 
    path('add_allergy/', child.ChildAlergyApiViews.as_view(), name='child_add_allergy'),
    path('parent_register_child/', child.parentResisterChild.as_view(), name='parent_register_child'),
    path('parent_validate_child_subscriber/<slug:slug>/', child.parentValidateChildDataAndLink.as_view(), name='parent_validate_child_subscriber'),
    path('child_parent_relationship/<slug:slug>/', child.ChildParentRelationship.as_view(), name='child_parent_relationship'),
    path('parent_list/<slug:slug>/', child.GetAllParentForthiChild.as_view(), name='parent_list'),
    # fin des routes qui conserne l'enfant  

    # les url sur le model qui link le parent au child
    path('lislinkchildtoparent/', views.lislinkchildtoparent.as_view(), name='lislinkchildtoparent'), 
    path('qr-code/<int:pk>/', views.GetQRCode.as_view(), name='get_qr_code'),
    path('tesspositionEnfantInZone/<slug:slug>/', parent.tesspositionEnfantInZone.as_view(), name='tesspositionEnfantInZone'),
    
    # Debut des url pour les divices 
    path('devices/', divice.AddDevice.as_view(), name='add-device'),  # POST = ajout device 
    path('devices/battery-status/', divice.BatteryStatusSave.as_view(), name='battery-status'),
    path('device/family-number/', divice.WellStockFamilyNumberForDevice.as_view(), name='family-number-device'),
    path('device/family-numbers/', divice.FamilyNumberView.as_view(), name='device/family-numbers/'),
    path('geolocaliser_par_wifi_mozilla/', divice.GeolocaliserParWifiMozilla.as_view(), name='geolocaliser_par_wifi_mozilla'),
    path('device_parent_to_family_member/', divice.ReleaseParentToDevice.as_view(), name='device_parent_to_family_member'),
    # Fin des url pour les divice 
]