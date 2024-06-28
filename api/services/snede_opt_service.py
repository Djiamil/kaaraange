import random
import string
from django.conf import settings
from api.models import *
import requests
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone





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
