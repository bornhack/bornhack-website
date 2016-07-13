from django.contrib import admin

from .models import Event, Speaker, EventType


@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'event_type',
        'get_days',
        'start',
        'end'
    ]

    def get_days(self, obj):
        return ', '.join([
            str(day.date.strftime('%a'))
            for day in obj.days.all()
        ])


@admin.register(Speaker)
class SpeakerAdmin(admin.ModelAdmin):
    pass


