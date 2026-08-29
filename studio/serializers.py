from rest_framework import serializers

from courses.models import Course
from sessions_app.models import Session

from .models import SlideTemplate


class SlideTemplateSerializer(serializers.ModelSerializer):
    created_by_matricule = serializers.PrimaryKeyRelatedField(source="created_by", read_only=True)

    class Meta:
        model = SlideTemplate
        fields = ["id", "name", "layout_type", "template_file", "created_by_matricule"]


class GeneratePosterSerializer(serializers.Serializer):
    """Payload de POST /api/studio/generate-poster/."""

    session_id = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all())
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=SlideTemplate.objects.all(),
        required=False,
        allow_null=True,
    )


class GenerateSlidesSerializer(serializers.Serializer):
    """Payload de POST /api/studio/generate-slides/."""

    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())


class GenerateSocialPostSerializer(serializers.Serializer):
    """Payload de POST /api/studio/generate-social-post/."""

    session_id = serializers.PrimaryKeyRelatedField(queryset=Session.objects.all())
