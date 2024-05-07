from django.conf import settings
from api.models import *
from rest_framework.response import Response
from rest_framework import status
import qrcode
from io import BytesIO
from django.core.files import File
from django.core.files.base import ContentFile
import base64
from django.http import HttpResponse
import logging
logger = logging.getLogger(__name__)


# fonction pour la generation du qrcode
def generate_qrcode_image(child_slug):
    try:
        # Générer le contenu du QRCode avec le slug de l'enfant
        qr_content = child_slug

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        # Créer un objet image pour le QRCode
        qr_img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        qr_img.save(buffer)
        return buffer.getvalue()
    except Exception as e:
        logger.exception("Une erreur s'est produite lors de la création du QR code : %s", e)
        return None