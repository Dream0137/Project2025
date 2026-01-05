from django.db import models
from django.conf import settings


class TableBooking(models.Model):
    """2TablesBooking"""
    table_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.table_name


class Timeslot(models.Model):
    """3Timeslots"""
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self) -> str:
        return f"{self.start_time} - {self.end_time}"


class Game(models.Model):
    """4Games"""
    game_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="game_images/", blank=True, null=True)
    stock = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return self.game_name

    def remaining_on(self, date, timeslot):
        """Remaining stock for a given booking_date + timeslot (ตามช่วงเวลา) counting Pending/Confirmed."""
        from django.db.models import Sum
        used = (
            BookingItem.objects
            .filter(booking__booking_date=date, booking__timeslot=timeslot, game=self)
            .exclude(booking__status="Cancelled")
            .aggregate(total=Sum("qty"))
            .get("total")
        ) or 0
        return max(self.stock - used, 0)


class Booking(models.Model):
    """5Bookings"""
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    table = models.ForeignKey(TableBooking, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    booking_date = models.DateField()
    party_size = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    customer_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("table", "timeslot", "booking_date")

    def __str__(self) -> str:
        return f"{self.user} - {self.table} - {self.booking_date}"


class BookingItem(models.Model):
    """6BookingItems"""
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="items")
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    def __str__(self) -> str:
        return f"{self.booking} - {self.game}"
