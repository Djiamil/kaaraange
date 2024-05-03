import random
import string
from django.conf import settings
from api.models import *
import requests
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone





# Fonction pour generer un code otp aleatoir de six chiffre
def generate_otp(user, phone_number):
    otp_code = ''.join(random.choices(string.digits, k=6)) 
    OTP.objects.create(user=user, otp_code=otp_code, phone_number=phone_number)
    return otp_code

def send_sms(data):
    try:
        # Construire le payload pour l'API Africa Mobile
        payload = {
            "accountid": data["accountid"],
            "password": data["password"],
            "sender": data["sender"],
            "ret_id": data.get("ret_id"),
            "ret_url": data.get("ret_url"),
            "text": data["text"],
            "to": data["to"],
            # Vous pouvez ajouter d'autres champs ici comme start_date, start_time, stop_time
        }

        # Appel à l'API Africa Mobile
        response = requests.post('https://lamsms.lafricamobile.com/api', json=payload)

        # Vérification de la réponse
        if response.status_code == 200:
            SMS.objects.create(
                accountid=data["accountid"],
                password=data["password"],
                sender=data["sender"],
                ret_id=data.get("ret_id"),
                ret_url=data.get("ret_url"),
                text=data["text"],
                to=data["to"],
                sent_at=timezone.now()
            )
            return Response({"message": "SMS envoyé avec succès"}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Erreur lors de l'envoi du SMS"}, status=status.HTTP_400_BAD_REQUEST)
    except requests.RequestException as e:
        return Response({"error": f"Erreur lors de la requête vers l'API Africa Mobile : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



