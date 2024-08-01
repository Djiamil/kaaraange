from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.admin_login, name='admin_login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('logout/', views.admin_logout, name='admin_logout'),
    path('dashboard/admins/', views.admin_list, name='admin_list'),
    path('add_admin/', views.UserApiViews.as_view(), name='add_admin'),
    path('admin_list/', views.admin_list_view, name='admin_list'),
    path('utilisateur_actif/', views.utilisateur_actif_view, name='utilisateur_actif'),
    path('utilisateur_inactif/', views.utilisateur_inactif_view, name='utilisateur_inactif'),
    path('parent_liste/', views.parent_liste_view, name='parent_liste'),
    path('child_liste/', views.child_liste_view, name='child_liste'),
    path('alert_list/', views.emergencyAlert_liste_view, name='alert_list'),
    path('update_alert_state/<int:alert_id>/', views.update_alert_state, name='update_alert_state'),
    path('leaflet_carte/', views.child_list_view, name='leaflet_carte'),
    path('child_details/<int:child_id>/', views.child_details_view, name='child_details'),
    path('parent_details/<int:parent_id>/', views.paren_details_view, name='parent_details'),
]
