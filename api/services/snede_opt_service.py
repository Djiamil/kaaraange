import random
import string
from django.conf import settings
from api.models import *
import requests
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from firebase_admin import credentials, messaging 
import math
from django.utils import timezone
from datetime import timedelta





# Fonction pour generer un code otp aleatoir de six chiffre
def generate_otp(pending_user=None):
    otp_code = ''.join(random.choices(string.digits, k=4))
    otp = OTP.objects.create(pending_user=pending_user,otp_code=otp_code)
    return otp_code

def regenerate_otp(pending_user=None):
    otp_code = ''.join(random.choices(string.digits, k=4))
    return otp_code

# gere les envoie sms des code otp et autre recoie numero et message
def send_sms(to_phone_number, text):
    try:
        # Informations fixes pour l'API Africa Mobile
        payload = {
            "accountid": "KAARAANGE",
            "password": "HdB9r878DgS7m",
            "sender": "KAARAANGE",
            "ret_id": "Push_1",
            "text": text,
            "to": [{"ret_id_1": to_phone_number}]
        }

        # Appel à l'API Africa Mobile
        response = requests.post('https://lamsms.lafricamobile.com/api', json=payload)

        # Vérification de la réponse
        if response.status_code == 200:
            SMS.objects.create(
                accountid="KAARAANGE",
                password="HdB9r878DgS7m",
                sender="KAARAANGE",
                ret_id="Push_1",
                text=text,
                to=to_phone_number,
            )
            return Response({"message": "SMS envoyé avec succès"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Erreur lors de l'envoi du SMS"}, status=status.HTTP_400_BAD_REQUEST)
    except requests.RequestException as e:
        return Response({"error": f"Erreur lors de la requête vers l'API Africa Mobile : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
# Fonction pour envoyer les notifications via firebase
def send_simple_notification(token,text):
    message = messaging.Message(
        notification=messaging.Notification(
            title='Bonjour,',
            body=text,
        ),
        token=token,
    )
    response = messaging.send(message)
    print('Successfully sent message:', response)

    
# Fonction pour calculer la distance entre deux points géographiques (formule de Haversine)
def calculer_distance(lat1, lon1, lat2, lon2):
    # Convertir les degrés en radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Différences entre les points
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Formule de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Rayon de la Terre en mètres (6,371 km)
    R = 6371000
    distance = R * c  # Résultat en mètres

    return distance

# Fonction principale pour vérifier si l'enfant est dans la zone de sécurité
def verifier_enfant_dans_zone(slug, lat_enfant, lon_enfant,adresse):
    try:
        # Récupérer le périmètre de sécurité associé à l'enfant
        perimetre_securite = PerimetreSecurite.objects.filter(enfant__slug=slug,is_active=True).first()
        
        # Récupérer le rayon du périmètre de sécurité
        rayon = perimetre_securite.rayon

        # Récupérer les coordonnées du point de référence
        point_trajet = perimetre_securite.point_trajet
        point_trajet_latitude = point_trajet.latitude
        point_trajet_longitude = point_trajet.longitude

        # Calculer la distance entre la position actuelle de l'enfant et le point de référence
        distance_enfant_point = calculer_distance(
            point_trajet_latitude, point_trajet_longitude, lat_enfant, lon_enfant
        )

        # Vérifier si la distance dépasse le rayon du périmètre de sécurité
        if distance_enfant_point <= rayon:
            return Response({
                'enfant_dans_zone': True,
                'distance': distance_enfant_point,
                'message': 'L\'enfant est dans la zone de sécurité.'
            }, status=status.HTTP_200_OK)
        
        else:
            # Envoi des alertes et notifications si l'enfant est hors de la zone
            try:
                child = Child.objects.filter(slug=slug).first()
                text = f"Vous avez reçu une alerte qui indique que votre enfant {child.prenom} est hors de sa zone de sécurité."

                # Récupérer la dernière alerte pour l'enfant
                child_alert = EmergencyAlert.objects.filter(child__slug=slug,alert_type="danger").last()
                if child_alert:
                # Si l'enfant a été hors de la zone pendant plus de 5 minutes
                    if child_alert and timezone.now() - child_alert.datetime_localisation >= timedelta(minutes=5):
                        alert = EmergencyAlert.objects.create(
                            child=child,
                            alert_type="danger",
                            comment=text,
                            latitude=lat_enfant,
                            longitude=lon_enfant,
                            adresse=adresse
                        )
                        
                        # Envoi des notifications aux membres de la famille et contacts d'urgence
                        family_members = FamilyMember.objects.filter(child=child)
                        emergency_contacts = []
                        for family_member in family_members:
                            parent = family_member.parent
                            if parent:
                                contacts = EmergencyContact.objects.filter(parent=parent)
                                for contact in contacts:
                                    emergency_contacts.append(contact)
                                if parent.fcm_token:
                                    token = parent.fcm_token
                                    try:
                                        send_simple_notification(token, text)
                                    except Exception as e:
                                        print(f"Erreur lors de l'envoi de la notification à {parent}: {e}")
                                AlertNotification.objects.create(alert=alert, type_notification='alerte', parent=parent)
                        for contact in emergency_contacts:
                            send_sms(contact.phone_number, text)
                        
                        return Response({
                            'enfant_dans_zone': False,
                            'distance': distance_enfant_point,
                            'message': 'Alerte ! L\'enfant est hors de la zone de sécurité. Alertes envoyées.'
                        }, status=status.HTTP_200_OK)
                    else:
                        # Si l'alerte a été envoyée il y a moins de 15 minutes, ne pas renvoyer
                        return Response({
                            'enfant_dans_zone': False,
                            'distance': distance_enfant_point,
                            'message': 'Alerte déjà envoyée récemment.'
                        }, status=status.HTTP_200_OK)
                else:
                    alert = EmergencyAlert.objects.create(
                            child=child,
                            alert_type="danger",
                            comment=text,
                            latitude=lat_enfant,
                            longitude=lon_enfant,
                            adresse=adresse
                        )
                    # Envoi des notifications aux membres de la famille et contacts d'urgence
                    family_members = FamilyMember.objects.filter(child=child)
                    emergency_contacts = []
                    for family_member in family_members:
                        parent = family_member.parent
                        if parent:
                            contacts = EmergencyContact.objects.filter(parent=parent)
                            for contact in contacts:
                                emergency_contacts.append(contact)
                            if parent.fcm_token:
                                token = parent.fcm_token
                                try:
                                    send_simple_notification(token, text)
                                except Exception as e:
                                    print(f"Erreur lors de l'envoi de la notification à {parent}: {e}")
                            AlertNotification.objects.create(alert=alert, type_notification='alerte', parent=parent)
                    for contact in emergency_contacts:
                        send_sms(contact.phone_number, text)
                    
                    return Response({
                        'enfant_dans_zone': False,
                        'distance': distance_enfant_point,
                        'message': 'Alerte ! L\'enfant est hors de la zone de sécurité. Alertes envoyées.dans le else'
                    }, status=status.HTTP_200_OK)
            except Child.DoesNotExist:
                return Response({
                    'data': None,
                    'message': 'Enfant non trouvé',
                    'success': False,
                    "code": 400
                }, status=status.HTTP_404_NOT_FOUND)
    
    except PerimetreSecurite.DoesNotExist:
        return Response({
            'enfant_dans_zone': False,
            'message': 'Aucun périmètre de sécurité trouvé pour cet enfant.'
        }, status=status.HTTP_404_NOT_FOUND)
