from django.shortcuts import render
# backoffice/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import *
from api.models import *
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse





def admin_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user is not None and (user.is_staff or user.user_type == 'ADMIN'):
                login(request, user)
                return redirect('admin_dashboard')
            else:
                form.add_error(None, 'Invalid email or password')
    else:
        form = LoginForm()
    return render(request, 'admin_login.html', {'form': form})

@login_required
def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')


@login_required
def admin_list(request):
    admins = User.objects.filter(user_type='ADMIN')
    return render(request, 'admin_list.html', {'admins': admins})

@login_required
def add_admin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_list')  # Assurez-vous que 'admin_list' est une URL valide
    else:
        form = AdminCreationForm()
    return render(request, 'add_admin.html', {'form': form})





class UserApiViews(generics.ListCreateAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        # Retourne uniquement les utilisateurs de type 'ADMIN'
        return User.objects.filter(user_type='ADMIN')

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            password = make_password(serializer.validated_data['password'])
            serializer.validated_data['password'] = password
            # Définit le type d'utilisateur comme 'ADMIN'
            serializer.validated_data['user_type'] = 'ADMIN'
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

def admin_list_view(request):
    users = User.objects.filter(user_type='ADMIN')
    return render(request, 'admin_list.html', {'users': users})



def utilisateur_actif_view(request):
    users = Parent.objects.all()
    parent_actif_liste = []
    parent_inactif_liste = []

    parents = Parent.objects.all()
    for parent in parents:
        parent_child_link = FamilyMember.objects.filter(parent=parent).exists()
        if parent_child_link:
            parent_actif_liste.append(parent)
        else:
            parent_inactif_liste.append(parent)
    return render(request, 'admin_list.html', {'users': parent_actif_liste})


def utilisateur_inactif_view(request):
    users = Parent.objects.all()
    parent_actif_liste = []
    parent_inactif_liste = []

    parents = Parent.objects.all()
    for parent in parents:
        parent_child_link = FamilyMember.objects.filter(parent=parent).exists()
        if parent_child_link:
            parent_actif_liste.append(parent)
        else:
            parent_inactif_liste.append(parent)
    return render(request, 'admin_list.html', {"users" :parent_inactif_liste})


def parent_liste_view(request):
    parent = Parent.objects.all()
    return render(request, 'admin_list.html', {"users" : parent})

def child_liste_view(request):
    parent = Child.objects.all()
    return render(request, 'admin_list.html', {"users" : parent})

def emergencyAlert_liste_view(request):
    # Sélectionnez toutes les alertes d'urgence en incluant les informations sur l'enfant associé
    alerts = EmergencyAlert.objects.select_related('child').all()
    return render(request, "alert_list.html", {"alerts": alerts})

def update_alert_state(request):
    if request.method == "POST":
        alert_id = request.POST.get("alert_id")
        try:
            alert = EmergencyAlert.objects.get(id=alert_id)
            alert.state = "traite"  # Mettez à jour l'état de l'alerte
            alert.save()
            return JsonResponse({"success": True})
        except EmergencyAlert.DoesNotExist:
            return JsonResponse({"success": False, "message": "Alert not found"})
    return JsonResponse({"success": False, "message": "Invalid request method"})



def child_list_view(request):
    children = Child.objects.all()
    return render(request, 'leaflet.html', {"children": children})

