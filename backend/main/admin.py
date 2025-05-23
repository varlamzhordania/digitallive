from django.contrib import admin
from nested_admin import NestedModelAdmin, NestedStackedInline

from .models import Place, Display, DisplayLog, DisplayToken, Ticker, TickerItem
from .forms import TickerItemForm

class TicketItemInline(NestedStackedInline):
    model = TickerItem
    form = TickerItemForm
    extra = 0


class TicketNestedInline(NestedStackedInline):
    model = Ticker
    extra = 0
    inlines = [TicketItemInline]


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'owner', 'is_active',
                    'updated_at', 'created_at']
    list_filter = ['is_active', 'updated_at', 'created_at']
    search_fields = ['owner__username', 'name']


@admin.register(Display)
class DisplayAdmin(NestedModelAdmin, admin.ModelAdmin):
    list_display = ['id', 'name', 'place', 'current_video',
                    'video_duration', 'loop', 'paused',
                    'is_active', 'updated_at', 'created_at']
    list_filter = ['loop', 'paused', 'is_active',
                   'updated_at', 'created_at']

    readonly_fields = ['task_id', 'stream_key', 'created_at', 'updated_at']

    search_fields = ['name', 'place__name']
    inlines = [TicketNestedInline]

    actions = ['set_video_duration_action', 'start_streaming_action', 'stop_streaming_action']

    def set_video_duration_action(self, request, queryset):
        """
        Action to Set Video Duration for selected displays.
        """
        for display in queryset:
            try:
                display.set_video_duration()
            except Exception as e:
                self.message_user(
                    request,
                    f"Error on setting video duration for {display.name}: {str(e)}",
                    level='error'
                )
            else:
                self.message_user(
                    request,
                    f"Video duration did set for {display.name} successfully."
                )

    def start_streaming_action(self, request, queryset):
        """
        Action to start streaming for selected displays.
        """
        for display in queryset:
            try:
                display.start_streaming()
            except Exception as e:
                self.message_user(
                    request,
                    f"Error starting stream for {display.name}: {str(e)}",
                    level='error'
                )
            else:
                self.message_user(
                    request,
                    f"Started stream for {display.name} successfully."
                )

    def stop_streaming_action(self, request, queryset):
        """
        Action to stop streaming for selected displays.
        """
        for display in queryset:
            try:
                display.pause_streaming()
            except Exception as e:
                self.message_user(
                    request,
                    f"Error stopping stream for {display.name}: {str(e)}",
                    level='error'
                )
            else:
                self.message_user(
                    request,
                    f"Stopped stream for {display.name} successfully."
                )

    set_video_duration_action.short_description = "Set Video Duration for selected displays."
    stop_streaming_action.short_description = "Stop streaming for selected displays"
    start_streaming_action.short_description = "Start streaming for selected displays"


@admin.register(DisplayLog)
class DisplayLogAdmin(admin.ModelAdmin):
    list_display = ["id", "display", "type", "created_at", "updated_at"]
    list_filter = ["type", "created_at", "updated_at"]

    search_fields = ["display__name", "display__stream_key", "display__id"]


@admin.register(DisplayToken)
class DisplayTokenAdmin(admin.ModelAdmin):
    list_display = ['key', 'display', 'created']
    fields = ['display']
    search_fields = ['key', 'display__name']
    ordering = ('-created',)