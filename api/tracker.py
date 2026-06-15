import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Device

TCP_SERVER = "http://127.0.0.1:9001"


# =====================================================
# UTILITAIRE — envoie une commande au TCP server
# =====================================================
def send_tracker_command(imei: str, command: str):
    try:
        response = requests.post(
            f"{TCP_SERVER}/command/",
            json={"imei": imei, "command": command},
            timeout=5
        )
        return response.json()
    except Exception as e:
        return {"success": False, "message": str(e)}


def get_device_or_error(imei):
    """Récupère le device par IMEI ou retourne une erreur."""
    try:
        return Device.objects.get(imei=imei), None
    except Device.DoesNotExist:
        return None, Response({
            "success": False,
            "message": "Device non trouvé",
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)


# =====================================================
# FIND — fait sonner le tracker pendant 1 minute
# =====================================================
class DeviceFind(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        result = send_tracker_command(imei, "FIND")
        if result.get("success"):
            return Response({
                "success": True,
                "message": "Le tracker sonne",
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": result.get("message", "Device non connecté"),
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)


# =====================================================
# POWEROFF — éteint le tracker à distance
# =====================================================
class DevicePowerOff(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        result = send_tracker_command(imei, "POWEROFF")
        if result.get("success"):
            return Response({
                "success": True,
                "message": "Tracker éteint",
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": result.get("message", "Device non connecté"),
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)


# =====================================================
# RESET — redémarre le tracker à distance
# =====================================================
class DeviceReset(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        result = send_tracker_command(imei, "RESET")
        if result.get("success"):
            return Response({
                "success": True,
                "message": "Tracker redémarré",
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": result.get("message", "Device non connecté"),
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)


# =====================================================
# SOS NUMBERS — configure les numéros SOS du tracker
# Le parent définit ses propres numéros depuis l'app
# =====================================================
class DeviceSetSOS(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        sos1 = request.data.get("sos1")
        sos2 = request.data.get("sos2")
        sos3 = request.data.get("sos3")

        if not sos1 and not sos2 and not sos3:
            return Response({
                "success": False,
                "message": "Au moins un numéro SOS requis (sos1, sos2 ou sos3)",
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        if sos1:
            r = send_tracker_command(imei, f"SOS1,{sos1}")
            results.append({"sos1": sos1, "success": r.get("success")})
        if sos2:
            r = send_tracker_command(imei, f"SOS2,{sos2}")
            results.append({"sos2": sos2, "success": r.get("success")})
        if sos3:
            r = send_tracker_command(imei, f"SOS3,{sos3}")
            results.append({"sos3": sos3, "success": r.get("success")})

        return Response({
            "success": True,
            "message": "Numéros SOS mis à jour",
            "data": results,
            "code": 200
        }, status=status.HTTP_200_OK)


# =====================================================
# CALL — fait appeler un numéro par le tracker
# =====================================================
class DeviceCall(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        number = request.data.get("number")
        if not number:
            return Response({
                "success": False,
                "message": "Numéro de téléphone requis",
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        result = send_tracker_command(imei, f"CALL,{number}")
        if result.get("success"):
            return Response({
                "success": True,
                "message": f"Appel vers {number} lancé",
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": result.get("message", "Device non connecté"),
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)


# =====================================================
# SCHEDULE — programme l'allumage/extinction du tracker
# =====================================================
class DeviceSchedule(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        hour   = request.data.get("hour")
        minute = request.data.get("minute", 0)
        action = request.data.get("action")  # "on" ou "off"
        week   = request.data.get("week", "1111111")  # tous les jours par défaut

        if hour is None or action not in ("on", "off"):
            return Response({
                "success": False,
                "message": "hour et action (on/off) requis",
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        type_val = 0 if action == "on" else 1
        command  = f"SPOF,{hour},{minute},1,0,{type_val},{week}"

        result = send_tracker_command(imei, command)
        if result.get("success"):
            return Response({
                "success": True,
                "message": f"Programmation {action} à {hour}h{minute:02d} configurée",
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": result.get("message", "Device non connecté"),
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)


# =====================================================
# STATUS — vérifie si le tracker est connecté au TCP
# =====================================================
class DeviceConnectionStatus(APIView):
    def get(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        try:
            response = requests.get(f"{TCP_SERVER}/status/", timeout=3)
            data = response.json()
            connected = imei in data.get("connected_devices", [])
            return Response({
                "success": True,
                "imei": imei,
                "connected": connected,
                "message": "En ligne" if connected else "Hors ligne",
                "code": 200
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e),
                "code": 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
# =====================================================
# TIMEZONE — règle le fuseau horaire du tracker
# Language: 0 = Anglais, 1 = Chinois
# Timezone: 0 = UTC, 1 = UTC+1, -5 = UTC-5, etc.
# Sénégal = UTC+0 donc timezone=0
# =====================================================
class DeviceSetTimezone(APIView):
    def post(self, request, imei):
        device, error = get_device_or_error(imei)
        if error:
            return error

        timezone = request.data.get("timezone")
        language = request.data.get("language", 0)  # 0=Anglais par défaut

        if timezone is None:
            return Response({
                "success": False,
                "message": "timezone requis (ex: 0 pour UTC, 1 pour UTC+1)",
                "code": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        result = send_tracker_command(imei, f"LZ,{language},{timezone}")
        if result.get("success"):
            return Response({
                "success": True,
                "message": f"Fuseau horaire réglé à UTC{'+' if int(timezone) >= 0 else ''}{timezone}",
                "code": 200
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": result.get("message", "Device non connecté"),
            "code": 404
        }, status=status.HTTP_404_NOT_FOUND)