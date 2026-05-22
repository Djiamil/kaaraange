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