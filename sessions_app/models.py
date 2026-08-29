from django.db import models

from courses.models import Course, Section
from inventory.models import Equipment


class Session(models.Model):
    """Seance du club : une date, un lieu, un theme, et le materiel reserve."""

    date = models.DateTimeField()
    location = models.CharField(max_length=255)
    theme = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    equipments = models.ManyToManyField(
        Equipment,
        through="SessionEquipment",
        related_name="sessions",
    )
    sections = models.ManyToManyField(
        Section,
        through="SessionSection",
        related_name="sessions",
    )

    class Meta:
        verbose_name = "seance"
        verbose_name_plural = "seances"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.theme} - {self.date:%d/%m/%Y}"


class SessionEquipment(models.Model):
    """Reservation d'une quantite de materiel pour une seance."""

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="equipment_reservations",
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    quantity_reserved = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "reservation de materiel"
        verbose_name_plural = "reservations de materiel"
        # Une seule ligne de reservation par couple seance/materiel.
        constraints = [
            models.UniqueConstraint(
                fields=["session", "equipment"],
                name="unique_equipment_per_session",
            )
        ]

    def __str__(self):
        return f"{self.equipment} x{self.quantity_reserved}"


class SessionSection(models.Model):
    """Section de cours effectivement abordee pendant une seance."""

    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="section_links")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="session_links")

    class Meta:
        verbose_name = "section abordee"
        verbose_name_plural = "sections abordees"
        constraints = [
            models.UniqueConstraint(
                fields=["session", "section"],
                name="unique_section_per_session",
            )
        ]

    def __str__(self):
        return f"{self.session_id} / {self.section_id}"
