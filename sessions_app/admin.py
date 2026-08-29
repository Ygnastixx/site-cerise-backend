from django.contrib import admin

from .models import Session, SessionEquipment, SessionSection


class SessionEquipmentInline(admin.TabularInline):
    model = SessionEquipment
    extra = 0


class SessionSectionInline(admin.TabularInline):
    model = SessionSection
    extra = 0


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ["id", "theme", "date", "location", "course"]
    list_filter = ["date", "location"]
    search_fields = ["theme", "description", "location"]
    inlines = [SessionEquipmentInline, SessionSectionInline]
