from django.contrib import admin
from .models import TableBooking, Timeslot, Game, Booking, BookingItem


@admin.register(TableBooking)
class TableBookingAdmin(admin.ModelAdmin):
    list_display = ('table_name', 'description')


@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('game_name',)


class BookingItemInline(admin.TabularInline):
    model = BookingItem
    extra = 1


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'table', 'booking_date', 'timeslot', 'party_size', 'status')
    list_filter = ('booking_date', 'status', 'table')
    inlines = [BookingItemInline]