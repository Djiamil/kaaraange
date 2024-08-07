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
from django.shortcuts import get_object_or_404
from api.serializers import *






def admin_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None:
                if user.is_staff or user.user_type == 'ADMIN':
                    login(request, user)
                    return redirect('admin_dashboard')
                else:
                    form.add_error(None, 'Vous n\'avez pas les permissions nécessaires pour accéder à cette interface.')
            else:
                form.add_error(None, 'Identifiant ou mot de passe incorrect.')
    else:
        form = LoginForm()

    return render(request, 'admin_login.html', {'form': form})

# @login_required
# def admin_dashboard(request):
#     return render(request, 'admin_dashboard.html')

def admin_dashboard(request):
    # Vous pouvez accéder aux détails de l'utilisateur via request.user
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'admin_dashboard.html', context)


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
    return render(request, 'utilisateur_actif.html', {'users': parent_actif_liste})


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
    return render(request, 'utilisateur_inactif.html', {"users" :parent_inactif_liste})

from django.core.paginator import Paginator

def parent_liste_view(request):
    # Réinitialiser la page courante si le paramètre de requête 'reset' est présent
    if request.GET.get('reset') == 'true':
        request.session.pop('currentPageParent', None)

    search_query = request.GET.get('search', '')  # Définir search_query en dehors de la condition

    # Récupérez le numéro de page et la taille de la page depuis la requête ou la session
    page_number = request.GET.get('page', request.session.get('currentPageParent', 1))
    page_size = request.GET.get('size', 10)
    
    # Récupérez les objets Parent
    parent_list = Parent.objects.all()
    if search_query:
        parent_list = parent_list.filter(prenom__icontains=search_query)
    
    # Configurez la pagination
    paginator = Paginator(parent_list, page_size)
    page = paginator.get_page(page_number)
    
    # Mettez à jour la session avec la page actuelle
    request.session['currentPageParent'] = page.number
    
    data = {
        "parent_actif_liste": list(page.object_list.values('id', 'email', 'phone_number', 'prenom', 'nom', 'adresse', 'avatar', 'is_active')),
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "number": page.number,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)
    
    return render(request, 'parent_liste.html', {"users": data['parent_actif_liste']})


def child_liste_view(request):
    # Réinitialiser la page courante si le paramètre de requête 'reset' est présent
    if request.GET.get('reset') == 'true':
        request.session.pop('current_page_child', None)
    
    # Récupérez le numéro de page et la taille de la page depuis la requête ou la session
    page_number = request.GET.get('page', request.session.get('current_page_child', 1))
    page_size = request.GET.get('size', 10)
    
    # Récupérez les objets Child
    child_list = Child.objects.all()
    
    # Configurez la pagination
    paginator = Paginator(child_list, page_size)
    page = paginator.get_page(page_number)
    
    # Mettez à jour la session avec la page actuelle
    request.session['current_page_child'] = page.number
    
    data = {
        "child_liste": list(page.object_list.values('id', 'email', 'phone_number', 'prenom', 'nom', 'avatar', 'is_active')),
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "number": page.number,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)
    
    return render(request, 'child_liste.html', {"users": data['child_liste']})

def child_details_view(request, child_id):
    child = get_object_or_404(Child, id=child_id)
    family_members = FamilyMember.objects.filter(child=child).select_related('parent')
    
    family_members_data = []
    for member in family_members:
        member_data = {
            "child": ChildSerializerDetail(child).data,
            "child_avatar" : child.avatar.url if child.avatar else None,
            "relation": member.relation,
            "parent_name": member.parent.nom,
            "parent_firstname": member.parent.prenom,
            "parent_email": member.parent.email,
            "parent_phone": member.parent.phone_number,
            "avatar_url": member.parent.avatar.url if member.parent.avatar else None,
        }
        family_members_data.append(member_data)
    
    return JsonResponse({"family_members": family_members_data})

def paren_details_view(request, parent_id):
    parent = get_object_or_404(Parent, id=parent_id)
    family_members = FamilyMember.objects.filter(parent=parent).select_related('child')

    family_members_data = []
    for member in family_members:
        member_data = {
            "parent": ParentSerializer(parent).data,
            "child_avatar": member.parent.avatar.url if member.parent.avatar else None,
            "relation": member.relation,
            "parent_name": member.child.nom,
            "parent_firstname": member.child.prenom,
            "parent_email": member.child.email,
            "parent_phone": member.child.phone_number,
            "avatar_url": parent.avatar.url if parent.avatar else None,
        }
        family_members_data.append(member_data)

    return JsonResponse({"family_members": family_members_data})

def emergencyAlert_liste_view(request):
    # Réinitialiser la page courante si le paramètre de requête 'reset' est présent
    if request.GET.get('reset') == 'true':
        request.session.pop('current_page_alert', None)
    
    # Récupérez le numéro de page et la taille de la page depuis la requête ou la session
    page_number = request.GET.get('page', request.session.get('current_page_alert', 1))
    page_size = request.GET.get('size', 10)
    search_query = request.GET.get('search', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    # Récupérez les objets EmergencyAlert avec filtre sur le prénom de l'enfant et dates
    alert_list = EmergencyAlert.objects.select_related('child')
    alert_list = alert_list.order_by('-alert_datetime')


    if search_query:
        alert_list = alert_list.filter(child__prenom__icontains=search_query)


    if start_date:
        alert_list = alert_list.filter(alert_datetime__gte=start_date)

    if end_date:
        alert_list = alert_list.filter(alert_datetime__lte=end_date)

    # Ajoutez l'ordre de tri par date décroissante
    
    # Configurez la pagination
    paginator = Paginator(alert_list, page_size)
    page = paginator.get_page(page_number)
    
    # Mettez à jour la session avec la page actuelle
    request.session['current_page_alert'] = page.number
    
    data = {
        "alerts": list(page.object_list.values('id', 'alert_type', 'comment', 'alert_datetime', 'state', 'child__prenom', 'child__nom', 'child__phone_number')),
        "has_next": page.has_next(),
        "has_previous": page.has_previous(),
        "number": page.number,
        "total_pages": paginator.num_pages,
        "total_count": paginator.count
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(data)
    
    return render(request, 'alert_list.html', {"alerts": data['alerts']})


def update_alert_state(request, alert_id):
    if request.method == "POST":
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

