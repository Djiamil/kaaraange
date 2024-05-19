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