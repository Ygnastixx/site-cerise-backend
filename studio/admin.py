from django.contrib import admin

from .models import SlideTemplate


@admin.register(SlideTemplate)
class SlideTemplateAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "layout_type", "created_by"]
    list_filter = ["layout_type"]
    search_fields = ["name"]
