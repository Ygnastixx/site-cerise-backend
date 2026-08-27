from django.db import models

# Create your models here.
class Session(models.Model):
    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    theme = models.CharField(max_length=255)
    description = models.TextField()
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )

    def __str__(self):
        return f"{self.theme} - {self.date}"

class SessionSection(models.Model):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="sections",
    )
    section = models.ForeignKey(
        "courses.Section",
        on_delete=models.CASCADE,
        related_name="sessions",
    )

    def __str__(self):
        return f"{self.session} - {self.section}"

class SessionEquipment(models.Model):
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="equipments",
    )
    equipment = models.ForeignKey(
        "inventory.Equipment",
        on_delete=models.CASCADE,
        related_name="session_reservations",
    )
    quantity_reserved = models.IntegerField()

    def __str__(self):
        return f"{self.equipment.name} - {self.quantity_reserved}"