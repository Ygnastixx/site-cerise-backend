from django.conf import settings
from django.db import models


class SlideTemplate(models.Model):
    """Gabarit visuel servant a produire une affiche ou un jeu de diapositives."""

    class LayoutType(models.TextChoices):
        POSTER = "POSTER", "Affiche"
        SLIDE = "SLIDE", "Diapositive"
        DOCUMENT = "DOCUMENT", "Document administratif"

    name = models.CharField(max_length=255)
    layout_type = models.CharField(
        max_length=20,
        choices=LayoutType.choices,
        default=LayoutType.SLIDE,
    )
    template_file = models.CharField(
        max_length=500,
        blank=True,
        help_text="Chemin ou identifiant du gabarit exploite par le Frontend.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="slide_templates",
        db_column="created_by_matricule",
    )

    class Meta:
        verbose_name = "gabarit"
        verbose_name_plural = "gabarits"
        ordering = ["name"]

    def __str__(self):
        return self.name
