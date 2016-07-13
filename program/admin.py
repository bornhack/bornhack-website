from django.contrib import admin

from .models import Event, Speaker, EventType


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    pass


