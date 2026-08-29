from django.db import models
from django.conf import settings
from .schemas import SECTION_SCHEMAS

def get_section_type_choices():
    """Génère automatiquement les choices Django à partir de SECTION_SCHEMAS."""
    return [(key, val.get('label', key)) for key, val in SECTION_SCHEMAS.items()]

class Course(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Brouillon'
        PUBLISHED = 'PUBLISHED', 'Publié'
        TRASH = 'TRASH', 'Corbeille'

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    is_template = models.BooleanField(default=False)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Section(models.Model):
    SECTION_TYPES = [
        ('TITLE', 'Titre / En-tête'),
        ('TEXT', 'Paragraphe Texte'),
        ('LIST', 'Liste à puces'),
        ('IMAGE', 'Image avec légende'),
        ('CODE', 'Extrait de code'),
        ('CALLOUT', 'Encart d\'attention'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subsections')
    title = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=get_section_type_choices())
    
    # Stockage JSON dynamique
    content = models.JSONField(default=dict, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.course.title} - {self.title}"
    