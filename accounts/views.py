from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegisterForm, LoginForm, ProfileForm


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = LoginForm(request)
    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def home_view(request):
    return render(request, "home.html")


@login_required
def profile_view(request):
    """หน้าดูและแก้ไขโปรไฟล์ผู้ใช้"""
    user = request.user

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "บันทึกข้อมูลโปรไฟล์เรียบร้อยแล้ว")
            return redirect("profile")
    else:
        form = ProfileForm(instance=user)

    # นับจำนวนการจองของผู้ใช้งาน
    from booking.models import Booking
    total_bookings = Booking.objects.filter(user=user).count()
    
    # ดึงการจองล่าสุด 5 รายการ
    recent_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:5]

    context = {
        "form": form,
        "total_bookings": total_bookings,
        "recent_bookings": recent_bookings,
    }
    return render(request, "accounts/profile.html", context)
