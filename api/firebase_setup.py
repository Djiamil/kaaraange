# firebase_setup.py
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    cred = credentials.Certificate("credentials/kaaraange-kids-firebase-adminsdk.json")
    firebase_admin.initialize_app(cred)