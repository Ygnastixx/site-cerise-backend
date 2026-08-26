from rest_framework import serializers
from .models import Course, Section


class SectionSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField(read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)
    parent_title = serializers.CharField(source="parent.title", read_only=True, allow_null=True)

    class Meta:
        model = Section
        fields = [
            "id", "course", "course_title", "parent", "parent_title", "title",
            "type", "content", "order", "children",
        ]

    def get_children(self, obj):
        return []

    def validate(self, attrs):
        course = attrs.get("course", getattr(self.instance, "course", None))
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        if parent and course and parent.course_id != course.id:
            raise serializers.ValidationError({"parent": "La section parente doit appartenir au même cours."})
        if self.instance and parent and parent.pk == self.instance.pk:
            raise serializers.ValidationError({"parent": "Une section ne peut pas être son propre parent."})
        return attrs


class CourseSerializer(serializers.ModelSerializer):
    author_matricule = serializers.CharField(source="author.matricule", read_only=True)
    author_username = serializers.CharField(source="author.username", read_only=True)
    sections_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "title", "description", "status", "is_template",
            "author_matricule", "author_username", "sections_count",
            "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "author_matricule", "author_username", "sections_count",
            "created_at", "updated_at",
        ]

    def get_sections_count(self, obj):
        return obj.sections.count()


class CourseDetailSerializer(CourseSerializer):
    sections = serializers.SerializerMethodField()

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ["sections"]

    def get_sections(self, obj):
        sections = list(obj.sections.all())
        by_parent = {}
        for section in sections:
            by_parent.setdefault(section.parent_id, []).append(section)

        def build(parent_id):
            return [
                {
                    "id": s.id,
                    "course": s.course_id,
                    "parent": s.parent_id,
                    "title": s.title,
                    "type": s.type,
                    "content": s.content,
                    "order": s.order,
                    "children": build(s.id),
                }
                for s in by_parent.get(parent_id, [])
            ]

        return build(None)


class SectionReorderSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())

    def validate_items(self, value):
        for item in value:
            if "id" not in item or "order" not in item:
                raise serializers.ValidationError("Chaque élément doit contenir id et order.")
            try:
                int(item["id"])
                int(item["order"])
            except (TypeError, ValueError):
                raise serializers.ValidationError("id et order doivent être numériques.")
        return value
