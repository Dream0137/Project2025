from django import forms
from django.contrib.auth import get_user_model

from .models import Booking, Game, TableBooking, Timeslot


BASE_INPUT_CLASS = (
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 "
    "text-sm outline-none focus:ring-2 focus:ring-slate-300"
)


class GameForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = ["game_name", "description", "image", "stock"]
        widgets = {
            "game_name": forms.TextInput(attrs={"class": BASE_INPUT_CLASS}),
            "description": forms.Textarea(
                attrs={"class": BASE_INPUT_CLASS, "rows": 4}
            ),
            "stock": forms.NumberInput(attrs={"class": BASE_INPUT_CLASS, "min": 0}),
        }


class TableForm(forms.ModelForm):
    class Meta:
        model = TableBooking
        fields = ["table_name", "description"]
        widgets = {
            "table_name": forms.TextInput(attrs={"class": BASE_INPUT_CLASS}),
            "description": forms.Textarea(attrs={"class": BASE_INPUT_CLASS, "rows": 3}),
        }


class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ["start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"class": BASE_INPUT_CLASS, "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": BASE_INPUT_CLASS, "type": "time"}),
        }


class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["status", "booking_date", "table", "timeslot", "party_size", "customer_name", "phone", "email", "notes"]
        widgets = {
            "status": forms.Select(attrs={"class": BASE_INPUT_CLASS}),
            "booking_date": forms.DateInput(attrs={"class": BASE_INPUT_CLASS, "type": "date"}),
            "table": forms.Select(attrs={"class": BASE_INPUT_CLASS}),
            "timeslot": forms.Select(attrs={"class": BASE_INPUT_CLASS}),
            "party_size": forms.NumberInput(attrs={"class": BASE_INPUT_CLASS, "min": 1}),
            "customer_name": forms.TextInput(attrs={"class": BASE_INPUT_CLASS}),
            "phone": forms.TextInput(attrs={"class": BASE_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": BASE_INPUT_CLASS}),
            "notes": forms.Textarea(attrs={"class": BASE_INPUT_CLASS, "rows": 3}),
        }


class UserAdminForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["username", "email", "name", "role", "status", "behavior_score", "is_staff", "is_superuser"]
        widgets = {
            "username": forms.TextInput(attrs={"class": BASE_INPUT_CLASS}),
            "email": forms.EmailInput(attrs={"class": BASE_INPUT_CLASS}),
            "name": forms.TextInput(attrs={"class": BASE_INPUT_CLASS}),
            "role": forms.Select(attrs={"class": BASE_INPUT_CLASS}),
            "status": forms.Select(attrs={"class": BASE_INPUT_CLASS}),
            "behavior_score": forms.NumberInput(attrs={"class": BASE_INPUT_CLASS}),
            "is_staff": forms.CheckboxInput(),
            "is_superuser": forms.CheckboxInput(),
        }
