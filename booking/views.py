from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.http import Http404
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.db import transaction

from .models import Booking, BookingItem, Game, TableBooking, Timeslot
from .forms import GameForm, TableForm, TimeslotForm, BookingAdminForm, UserAdminForm

User = get_user_model()


def admin_required(view_func):
    """Allow either Django staff/superuser OR custom role=admin."""
    from functools import wraps

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        u = request.user
        if getattr(u, "is_superuser", False) or getattr(u, "is_staff", False) or getattr(u, "role", "") == "admin":
            return view_func(request, *args, **kwargs)
        raise Http404
    return _wrapped


@login_required
def select_date(request):
    """Step 1 – เลือกวันที่จอง"""
    if request.method == "POST":
        date_str = request.POST.get("booking_date")
        if not date_str:
            messages.error(request, "กรุณาเลือกวันที่")
        else:
            url = reverse("select_timeslot") + f"?date={date_str}"
            return redirect(url)
    return render(request, "booking/select_date.html")


@login_required
def select_timeslot(request):
    """
    Step 2 – เลือกโต๊ะและ 'หลาย' ช่วงเวลาในวันที่เลือกได้
    - แสดงโต๊ะทุกโต๊ะ + slot เวลา
    - ช่องที่ถูกจองแล้ว (ยกเลิกไม่นับ) จะขึ้นแดงและกดไม่ได้
    - ช่องว่างเลือกได้หลายช่องด้วย checkbox แต่ต้องเป็นโต๊ะเดียวกัน
    """

    date_str = request.GET.get("date") or request.POST.get("booking_date")
    if not date_str:
        return redirect("select_date")

    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
        return redirect("select_date")

    tables = list(TableBooking.objects.all().order_by("table_name"))
    timeslots = list(Timeslot.objects.all().order_by("start_time"))

    bookings = Booking.objects.filter(
        booking_date=booking_date
    ).exclude(status="Cancelled")

    booked_map = {}
    for b in bookings:
        booked_map.setdefault(b.table_id, set()).add(b.timeslot_id)

    for t in tables:
        t.booked_slot_ids = booked_map.get(t.id, set())

    if request.method == "POST":
        selected = request.POST.getlist("slots")
        if not selected:
            messages.error(request, "กรุณาเลือกโต๊ะและช่วงเวลาอย่างน้อย 1 ช่วงเวลา")
        else:
            pairs = []
            for value in selected:
                try:
                    table_id_str, slot_id_str = value.split("-")
                    pairs.append((int(table_id_str), int(slot_id_str)))
                except ValueError:
                    continue

            if not pairs:
                messages.error(request, "ข้อมูลช่วงเวลาไม่ถูกต้อง")
            else:
                table_ids = {p[0] for p in pairs}
                if len(table_ids) > 1:
                    messages.error(request, "กรุณาเลือกช่วงเวลาภายในโต๊ะเดียวกันเท่านั้น")
                else:
                    table_id = pairs[0][0]
                    timeslot_ids = [str(p[1]) for p in pairs]
                    timeslots_param = ",".join(timeslot_ids)
                    url = (
                        reverse("select_game")
                        + f"?date={booking_date}&table={table_id}&timeslots={timeslots_param}"
                    )
                    return redirect(url)

    context = {
        "booking_date": booking_date,
        "tables": tables,
        "timeslots": timeslots,
    }
    return render(request, "booking/select_timeslot.html", context)


@login_required
@login_required
def select_game(request):
    """Step 3 – เลือกเกม (เลือกได้หลายเกม) สำหรับโต๊ะ + หลายช่วงเวลาที่เลือก
    เลือกเป็น "จำนวนต่อเกม" (0 = ไม่เลือก) และแสดงจำนวนคงเหลือในช่วงเวลาที่เลือก (ตามช่วงเวลา)
    """

    date_str = request.GET.get("date")
    table_id = request.GET.get("table") or request.GET.get("table_id")
    timeslots_param = request.GET.get("timeslots") or request.GET.get("timeslot")

    if not (date_str and table_id and timeslots_param):
        return redirect("select_date")

    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
        return redirect("select_date")

    table = get_object_or_404(TableBooking, pk=table_id)

    timeslot_ids = [int(x) for x in timeslots_param.split(",") if x]
    timeslots = list(Timeslot.objects.filter(id__in=timeslot_ids).order_by("start_time"))
    if not timeslots:
        messages.error(request, "ไม่พบช่วงเวลาที่เลือก")
        return redirect("select_timeslot")

    start_time = timeslots[0].start_time
    end_time = timeslots[-1].end_time

    games = list(Game.objects.all().order_by("game_name"))
    for g in games:
        g.remaining = min(g.remaining_on(booking_date, t) for t in timeslots)

    context = {
        "booking_date": booking_date,
        "table": table,
        "timeslots": timeslots,
        "timeslot_ids": ",".join(str(t.id) for t in timeslots),
        "start_time": start_time,
        "end_time": end_time,
        "games": games,
    }
    return render(request, "booking/select_game.html", context)



@login_required
@login_required
def booking_summary(request):
    """Step 4 – สรุปการจอง + รับข้อมูลลูกค้า รองรับหลาย timeslot
    รับเกมแบบหลายเกมพร้อมจำนวน: qty_<game_id> (0 = ไม่เลือก)
    """
    if request.method != "POST":
        return redirect("select_date")

    date_str = request.POST.get("date")
    table_id = request.POST.get("table_id")
    timeslot_ids_param = request.POST.get("timeslot_ids", "")
    party_size_raw = request.POST.get("party_size") or "2"

    # parse selected games (qty > 0)
    selected_pairs = []
    for k, v in request.POST.items():
        if not k.startswith("qty_"):
            continue
        try:
            gid = int(k.split("_", 1)[1])
            qty = int(v or 0)
        except (ValueError, IndexError):
            continue
        if qty > 0:
            selected_pairs.append((gid, qty))

    if not selected_pairs:
        messages.error(request, "กรุณาเลือกอย่างน้อย 1 เกม")
        url = (
            reverse("select_game")
            + f"?date={date_str}&table={table_id}&timeslots={timeslot_ids_param}"
        )
        return redirect(url)

    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
        return redirect("select_date")

    try:
        party_size = int(party_size_raw)
    except ValueError:
        party_size = 2

    table = get_object_or_404(TableBooking, pk=table_id)

    timeslot_ids = [int(x) for x in timeslot_ids_param.split(",") if x]
    timeslots = list(Timeslot.objects.filter(id__in=timeslot_ids).order_by("start_time"))
    if not timeslots:
        messages.error(request, "ไม่พบช่วงเวลาที่เลือก")
        return redirect("select_timeslot")

    start_time = timeslots[0].start_time
    end_time = timeslots[-1].end_time

    # fetch games and attach remaining info
    selected_ids = [gid for gid, _qty in selected_pairs]
    games_qs = Game.objects.filter(pk__in=selected_ids).order_by("game_name")
    games_map = {g.id: g for g in games_qs}

    selected_games = []
    for gid, qty in selected_pairs:
        g = games_map.get(gid)
        if not g:
            continue
        selected_games.append({
            "game": g,
            "qty": qty,
            "remaining": min(g.remaining_on(booking_date, t) for t in timeslots),
        })

    context = {
        "booking_date": booking_date,
        "table": table,
        "timeslots": timeslots,
        "timeslot_ids": timeslot_ids_param,
        "start_time": start_time,
        "end_time": end_time,
        "selected_games": selected_games,
        "party_size": party_size,
        "name": request.user.get_full_name() or request.user.username,
        "phone": "",
        "email": request.user.email,
    }
    return render(request, "booking/booking_summary.html", context)



@login_required
@login_required
@transaction.atomic
def booking_success(request):
    """Step 5 – บันทึกการจอง (หลายช่วงเวลา) แล้วแสดงหน้าสำเร็จ
    - ตรวจสอบ/หักจำนวนเกมตาม "ช่วงเวลา" (ไม่นับ Cancelled) (ไม่นับ Cancelled)
    - รองรับหลายเกม + จำนวน (game_ids + game_qtys)
    """
    if request.method != "POST":
        return redirect("select_date")

    date_str = request.POST.get("date")
    table_id = request.POST.get("table_id")
    timeslot_ids_param = request.POST.get("timeslot_ids", "")
    game_ids = request.POST.getlist("game_ids")
    game_qtys = request.POST.getlist("game_qtys")
    party_size_raw = request.POST.get("party_size") or "2"

    name = request.POST.get("name") or request.user.get_full_name()
    phone = request.POST.get("phone") or ""
    email = request.POST.get("email") or request.user.email

    if not game_ids:
        messages.error(request, "กรุณาเลือกอย่างน้อย 1 เกม")
        url = (
            reverse("select_game")
            + f"?date={date_str}&table={table_id}&timeslots={timeslot_ids_param}"
        )
        return redirect(url)

    if len(game_ids) != len(game_qtys):
        messages.error(request, "ข้อมูลจำนวนเกมไม่ครบถ้วน กรุณาเลือกใหม่")
        url = (
            reverse("select_game")
            + f"?date={date_str}&table={table_id}&timeslots={timeslot_ids_param}"
        )
        return redirect(url)

    # build requirements dict
    game_reqs = {}
    for gid, qty in zip(game_ids, game_qtys):
        try:
            gid_int = int(gid)
            qty_int = int(qty)
        except ValueError:
            continue
        if qty_int <= 0:
            continue
        game_reqs[gid_int] = game_reqs.get(gid_int, 0) + qty_int

    if not game_reqs:
        messages.error(request, "กรุณาเลือกอย่างน้อย 1 เกม")
        url = (
            reverse("select_game")
            + f"?date={date_str}&table={table_id}&timeslots={timeslot_ids_param}"
        )
        return redirect(url)

    try:
        booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        messages.error(request, "รูปแบบวันที่ไม่ถูกต้อง")
        return redirect("select_date")

    try:
        party_size = int(party_size_raw)
    except ValueError:
        party_size = 2

    table = get_object_or_404(TableBooking, pk=table_id)

    timeslot_ids = [int(x) for x in timeslot_ids_param.split(",") if x]
    timeslots = list(Timeslot.objects.filter(id__in=timeslot_ids).order_by("start_time"))
    if not timeslots:
        messages.error(request, "ไม่พบช่วงเวลาที่เลือก")
        return redirect("select_timeslot")

    # check slot availability first
    for tslot in timeslots:
        if Booking.objects.filter(
            table=table,
            timeslot=tslot,
            booking_date=booking_date,
        ).exclude(status="Cancelled").exists():
            messages.error(
                request,
                f"โต๊ะ {table.table_name} ช่วงเวลา {tslot.start_time:%H:%M}-{tslot.end_time:%H:%M} ถูกจองไปแล้ว",
            )
            url = reverse("select_timeslot") + f"?date={booking_date}"
            return redirect(url)

    # lock selected games and validate remaining stock (ตามช่วงเวลา)
    locked_games = list(Game.objects.select_for_update().filter(id__in=list(game_reqs.keys())).order_by("id"))
    locked_map = {g.id: g for g in locked_games}

    for gid, qty in game_reqs.items():
        g = locked_map.get(gid)
        if not g:
            messages.error(request, "ไม่พบเกมที่เลือก")
            url = (
                reverse("select_game")
                + f"?date={date_str}&table={table_id}&timeslots={timeslot_ids_param}"
            )
            return redirect(url)

        # ตรวจสอบคงเหลือของทุกช่วงเวลาที่เลือก (ใช้สถานะที่ไม่ใช่ Cancelled)
        for tslot in timeslots:
            remaining = g.remaining_on(booking_date, tslot)
            if qty > remaining:
                messages.error(
                    request,
                    f"เกม '{g.game_name}' เหลือ {remaining} ชุดในช่วงเวลา {tslot.start_time:%H:%M}-{tslot.end_time:%H:%M} ของวันที่เลือก"
                )
                url = (
                    reverse("select_game")
                    + f"?date={date_str}&table={table_id}&timeslots={timeslot_ids_param}"
                )
                return redirect(url)

    # create bookings (per timeslot) – attach game items to each record (นับสต็อกตามช่วงเวลา)
    bookings = []
    for tslot in timeslots:
        booking = Booking.objects.create(
            user=request.user,
            table=table,
            timeslot=tslot,
            booking_date=booking_date,
            party_size=party_size,
            customer_name=name,
            phone=phone,
            email=email,
            status="Pending",
        )
        bookings.append(booking)

        # บันทึกรายการเกมที่จอง (หลายเกม + จำนวน) ให้กับ booking ของช่วงเวลานี้
        for gid, qty in game_reqs.items():
            BookingItem.objects.create(booking=booking, game=locked_map[gid], qty=qty)

    games = list(Game.objects.filter(pk__in=list(game_reqs.keys())).order_by("game_name"))

    context = {
        "bookings": bookings,
        "games": games,
        "booking_date": booking_date,
        "table": table,
        "start_time": timeslots[0].start_time,
        "end_time": timeslots[-1].end_time,
    }
    return render(request, "booking/booking_success.html", context)



@login_required
def booking_history(request):
    """ประวัติการจองของผู้ใช้"""
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related("table", "timeslot")
        .order_by("-booking_date", "timeslot__start_time")
    )
    return render(request, "booking/booking_history.html", {"bookings": bookings})


@login_required
def cancel_booking(request, pk):
    """ยกเลิกการจอง (เปลี่ยนสถานะเป็น Cancelled)"""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if request.method == "POST":
        booking.status = "Cancelled"
        booking.save()
        messages.success(request, "ยกเลิกการจองเรียบร้อยแล้ว")
        return redirect("booking_history")

    return render(request, "booking/confirm_cancel.html", {"booking": booking})


# =========================
#        ADMIN VIEWS
# =========================

@admin_required
def admin_dashboard(request):
    """Dashboard แอดมิน – สรุปจำนวนการจองวันนี้"""
    today = timezone.localdate()

    today_qs = Booking.objects.filter(booking_date=today)
    all_qs = Booking.objects.all()

    stats = {
        # Today
        "today_total": today_qs.count(),
        "today_pending": today_qs.filter(status="Pending").count(),
        "today_confirmed": today_qs.filter(status="Confirmed").count(),
        "today_cancelled": today_qs.filter(status="Cancelled").count(),
        # Overall
        "all_total": all_qs.count(),
        "all_pending": all_qs.filter(status="Pending").count(),
        "all_confirmed": all_qs.filter(status="Confirmed").count(),
        "all_cancelled": all_qs.filter(status="Cancelled").count(),
        # Master data
        "table_count": TableBooking.objects.count(),
        "timeslot_count": Timeslot.objects.count(),
        "game_count": Game.objects.count(),
        "customer_count": User.objects.count(),
    }

    # 7-day trend (including today)
    start = today - timezone.timedelta(days=6)
    trend_qs = (
        Booking.objects
        .filter(booking_date__range=(start, today))
        .values("booking_date")
        .annotate(total=Count("id"))
        .order_by("booking_date")
    )
    # Fill missing dates
    trend_map = {row["booking_date"]: row["total"] for row in trend_qs}
    trend_labels = []
    trend_values = []
    for i in range(7):
        d = start + timezone.timedelta(days=i)
        trend_labels.append(d.strftime("%Y-%m-%d"))
        trend_values.append(int(trend_map.get(d, 0)))

    # Status distribution (overall)
    dist = {
        "Pending": stats["all_pending"],
        "Confirmed": stats["all_confirmed"],
        "Cancelled": stats["all_cancelled"],
    }

    recent = (
        Booking.objects
        .select_related("table", "timeslot", "user")
        .order_by("-created_at")[:8]
    )

    context = {
        "today": today,
        "stats": stats,
        "trend_labels": trend_labels,
        "trend_values": trend_values,
        "status_dist": dist,
        "recent": recent,
    }
    return render(request, "admin/admin_dashboard.html", context)


@admin_required
def admin_booking_list(request):
    """หน้า Booking Management สำหรับแอดมิน"""
    qs = (
        Booking.objects
        .select_related("table", "timeslot", "user")
        .order_by("-booking_date", "timeslot__start_time")
    )
    return render(request, "admin/admin_booking_list.html", {"bookings": qs})


@admin_required
def admin_store_management(request):
    """หน้า Store Management – จัดการเกม"""
    games = Game.objects.all().order_by("game_name")
    return render(request, "admin/admin_store_management.html", {"games": games})


@admin_required
def admin_customer_list(request):
    """หน้า Customer Data Management"""
    customers = User.objects.all().order_by("username")
    return render(request, "admin/admin_customer_list.html", {"customers": customers})


# =========================
#        ADMIN CRUD
# =========================


@admin_required
def admin_game_create(request):
    form = GameForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "เพิ่มเกมเรียบร้อยแล้ว")
        return redirect("admin_store_management")
    return render(request, "admin/admin_form.html", {"title": "เพิ่มเกม", "form": form, "back_url": reverse("admin_store_management")})


@admin_required
def admin_game_update(request, pk):
    game = get_object_or_404(Game, pk=pk)
    form = GameForm(request.POST or None, request.FILES or None, instance=game)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "แก้ไขเกมเรียบร้อยแล้ว")
        return redirect("admin_store_management")
    return render(request, "admin/admin_form.html", {"title": f"แก้ไขเกม: {game.game_name}", "form": form, "back_url": reverse("admin_store_management")})


@admin_required
def admin_game_delete(request, pk):
    game = get_object_or_404(Game, pk=pk)
    if request.method == "POST":
        game.delete()
        messages.success(request, "ลบเกมเรียบร้อยแล้ว")
        return redirect("admin_store_management")
    return render(request, "admin/admin_confirm_delete.html", {"title": "ลบเกม", "object_name": game.game_name, "back_url": reverse("admin_store_management")})


@admin_required
def admin_table_list(request):
    tables = TableBooking.objects.all().order_by("table_name")
    return render(request, "admin/admin_table_list.html", {"tables": tables})


@admin_required
def admin_table_create(request):
    form = TableForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "เพิ่มโต๊ะเรียบร้อยแล้ว")
        return redirect("admin_table_list")
    return render(request, "admin/admin_form.html", {"title": "เพิ่มโต๊ะ", "form": form, "back_url": reverse("admin_table_list")})


@admin_required
def admin_table_update(request, pk):
    table = get_object_or_404(TableBooking, pk=pk)
    form = TableForm(request.POST or None, instance=table)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "แก้ไขโต๊ะเรียบร้อยแล้ว")
        return redirect("admin_table_list")
    return render(request, "admin/admin_form.html", {"title": f"แก้ไขโต๊ะ: {table.table_name}", "form": form, "back_url": reverse("admin_table_list")})


@admin_required
def admin_table_delete(request, pk):
    table = get_object_or_404(TableBooking, pk=pk)
    if request.method == "POST":
        table.delete()
        messages.success(request, "ลบโต๊ะเรียบร้อยแล้ว")
        return redirect("admin_table_list")
    return render(request, "admin/admin_confirm_delete.html", {"title": "ลบโต๊ะ", "object_name": table.table_name, "back_url": reverse("admin_table_list")})


@admin_required
def admin_booking_create(request):
    form = BookingAdminForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        if not booking.user_id:
            booking.user = request.user
        booking.save()
        messages.success(request, "เพิ่มการจองเรียบร้อยแล้ว")
        return redirect("admin_booking_list")
    return render(request, "admin/admin_form.html", {"title": "เพิ่มการจอง", "form": form, "back_url": reverse("admin_booking_list")})


@admin_required
def admin_booking_update(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    form = BookingAdminForm(request.POST or None, instance=booking)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "แก้ไขการจองเรียบร้อยแล้ว")
        return redirect("admin_booking_list")
    return render(request, "admin/admin_form.html", {"title": f"แก้ไขการจอง #{booking.id}", "form": form, "back_url": reverse("admin_booking_list")})


@admin_required
def admin_booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == "POST":
        booking.delete()
        messages.success(request, "ลบการจองเรียบร้อยแล้ว")
        return redirect("admin_booking_list")
    return render(request, "admin/admin_confirm_delete.html", {"title": "ลบการจอง", "object_name": f"Booking #{booking.id}", "back_url": reverse("admin_booking_list")})


@admin_required
def admin_customer_update(request, pk):
    customer = get_object_or_404(User, pk=pk)
    form = UserAdminForm(request.POST or None, instance=customer)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "อัปเดตข้อมูลผู้ใช้เรียบร้อยแล้ว")
        return redirect("admin_customer_list")
    return render(request, "admin/admin_form.html", {"title": f"แก้ไขผู้ใช้: {customer.username}", "form": form, "back_url": reverse("admin_customer_list")})


@admin_required
def admin_customer_delete(request, pk):
    customer = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        customer.delete()
        messages.success(request, "ลบผู้ใช้เรียบร้อยแล้ว")
        return redirect("admin_customer_list")
    return render(request, "admin/admin_confirm_delete.html", {"title": "ลบผู้ใช้", "object_name": customer.username, "back_url": reverse("admin_customer_list")})