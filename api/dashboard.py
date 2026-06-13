from api.serializers import *
from api.models import *
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from django.db.models.functions import TruncMonth
import calendar
from datetime import date

from rest_framework.views import APIView







class AdminStatsView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({
            "users": get_user_stats(),
            "devices": get_device_stats(),
            "notifications": get_notification_stats(),
            "security": get_security_stats(),
            "sms": get_sms_stats(),
            "alerts": get_alert_stats(),
            "age_distribution": get_age_distribution_stats(),
            "weekly_registrations": get_weekly_registrations_stats(),
            "meta": {
                "generated_at": timezone.now()
            }
        })
        
def get_user_stats():
    current_year = timezone.now().year

    qs = (
        User.objects
        .filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
    )

    # transformer en dict {mois: count}
    data_map = {
        item["month"].month: item["count"]
        for item in qs
    }

    # construire les 12 mois
    result = []
    for m in range(1, 13):
        result.append({
            "month": calendar.month_name[m],
            "count": data_map.get(m, 0)
        })

    return {
        "total_users": User.objects.count(),
        "parents": Parent.objects.count(),
        "children": Child.objects.count(),
        "by_type": list(
            User.objects.values("user_type").annotate(count=Count("id"))
        ),
        "registrations_by_month": result
    }
    
def get_device_stats():
    return {
        "total": Device.objects.count(),
        "by_model": list(
            Device.objects.values("model_name")
            .annotate(count=Count("id"))
        )
    }
    
    
def get_notification_stats():
    return {
        "total": AlertNotification.objects.count(),
        "in_progress": AlertNotification.objects.filter(status="en_cours").count(),
        "accepted": AlertNotification.objects.filter(status="accepté").count(),
        "refused": AlertNotification.objects.filter(status="refusé").count(),
        "by_type": list(
            AlertNotification.objects.values("type_notification")
            .annotate(count=Count("id"))
        )
    }
    
    
    
def get_security_stats():
    return {
        "active_perimeters": PerimetreSecurite.objects.filter(is_active=True).count(),
        "inactive_perimeters": PerimetreSecurite.objects.filter(is_active=False).count(),
        "total_perimeters": PerimetreSecurite.objects.count()
    }
    
def get_sms_stats():
    current_year = timezone.now().year

    qs = (
        SMS.objects
        .filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
    )

    data_map = {
        item["month"].month: item["count"]
        for item in qs
    }

    result = []

    for m in range(1, 13):
        result.append({
            "month": calendar.month_name[m],
            "count": data_map.get(m, 0)
        })

    return {
        "total_sms": SMS.objects.count(),
        "sms_by_month": result
    }
    
def get_alert_stats():
    current_year = timezone.now().year

    # Alertes groupées par mois
    alerts_by_month_queryset = (
        EmergencyAlert.objects
        .filter(alert_datetime__year=current_year)
        .annotate(month=TruncMonth("alert_datetime"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    # Initialiser tous les mois à 0
    months_data = {
        month: 0 for month in range(1, 13)
    }

    # Remplir avec les vraies valeurs
    for item in alerts_by_month_queryset:
        months_data[item["month"].month] = item["count"]

    # Format frontend
    alerts_by_month = [
        {
            "month": calendar.month_name[month],
            "count": count
        }
        for month, count in months_data.items()
    ]

    return {
        "total": EmergencyAlert.objects.count(),

        "pending": EmergencyAlert.objects.filter(
            state="en_attente"
        ).count(),

        "processed": EmergencyAlert.objects.filter(
            state="traite"
        ).count(),

        "by_type": list(
            EmergencyAlert.objects
            .values("alert_type")
            .annotate(count=Count("id"))
        ),

        "alerts_by_month": alerts_by_month
    }
    
def get_age_distribution_stats():

    intervals = {
        "0-5": 0,
        "6-8": 0,
        "9-12": 0,
        "13-15": 0,
        "16-18": 0,
    }

    total = Child.objects.count()

    if total == 0:
        return {
            "total_enfants": 0,
            "repartition": []
        }

    today = date.today()

    for child in Child.objects.all():

        age = (
            today.year
            - child.date_de_naissance.year
            - (
                (today.month, today.day)
                < (
                    child.date_de_naissance.month,
                    child.date_de_naissance.day
                )
            )
        )

        if 0 <= age <= 5:
            intervals["0-5"] += 1

        elif 6 <= age <= 8:
            intervals["6-8"] += 1

        elif 9 <= age <= 12:
            intervals["9-12"] += 1

        elif 13 <= age <= 15:
            intervals["13-15"] += 1

        elif 16 <= age <= 18:
            intervals["16-18"] += 1

    return {
        "total_enfants": total,
        "repartition": [
            {
                "interval": interval_name,
                "count": count,
                "percentage": round((count / total) * 100, 2)
            }
            for interval_name, count in intervals.items()
        ]
    }
    
def get_weekly_registrations_stats():
    """
    Liste des utilisateurs inscrits cette semaine.
    """

    start_date = timezone.now() - timedelta(days=7)

    users = User.objects.filter(
        created_at__gte=start_date
    ).order_by('-created_at')

    return {
        "total": users.count(),
        "users": [
            {
                "prenom": user.prenom,
                "nom": user.nom,
                "user_type": user.user_type,
                "created_at": user.created_at.strftime("%d/%m/%Y")
            }
            for user in users
        ]
    }