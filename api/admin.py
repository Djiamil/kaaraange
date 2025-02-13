from django.contrib import admin

# Register your models here.

from api.models import *

class UserAdmin(admin.ModelAdmin):

    search_fields = ("email",)

admin.site.register(User, UserAdmin)
admin.site.register(Parent)
admin.site.register(Child)
admin.site.register(ParentChildLink)
admin.site.register(FamilyMember)
admin.site.register(PendingUser)
admin.site.register(OTP)
admin.site.register(SMS)
admin.site.register(Location)
admin.site.register(Allergy)
admin.site.register(EmergencyAlert)
admin.site.register(EmergencyNumber)
admin.site.register(EmergencyContact)
admin.site.register(MedicalIssue)
admin.site.register(AlertNotification)
admin.site.register(PointTrajet)
admin.site.register(PerimetreSecurite)
admin.site.register(Demande)
admin.site.register(ChildWithPerimetreSecurite)