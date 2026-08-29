from rest_framework import serializers
from .models import Section, Course
from .schemas import SECTION_SCHEMAS

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
            # Validation d'appartenance au même cours (ton code existant)
            course = attrs.get("course", getattr(self.instance, "course", None))
            parent = attrs.get("parent", getattr(self.instance, "parent", None))
            if parent and course and parent.course_id != course.id:
                raise serializers.ValidationError({"parent": "La section parente doit appartenir au même cours."})
            if self.instance and parent and parent.pk == self.instance.pk:
                raise serializers.ValidationError({"parent": "Une section ne peut pas être son propre parent."})

            # --- NOUVELLE VALIDATION : Vérification du schéma JSON ---
            section_type = attrs.get("type", getattr(self.instance, "type", None))
            content = attrs.get("content", getattr(self.instance, "content", {}))

            if section_type in SECTION_SCHEMAS:
                fields_config = SECTION_SCHEMAS[section_type].get("fields", {})
                for field_name, field_info in fields_config.items():
                    if field_info.get("required") and field_name not in content:
                        raise serializers.ValidationError({
                            "content": f"Le champ '{field_name}' est obligatoire pour une section de type '{section_type}'."
                        })

            return attrs


class SectionNestedSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    children = serializers.ListField(child=serializers.DictField(), required=False, default=list)

    class Meta:
        model = Section
        fields = ['id', 'title', 'type', 'content', 'order', 'children']

class CourseSerializer(serializers.ModelSerializer):
    sections = SectionNestedSerializer(many=True, required=False, default=list)
    author_matricule = serializers.CharField(source="author.matricule", read_only=True) # <-- AJOUTER ICI

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'status', 'is_template', 
            'author', 'author_matricule', 'sections', 'created_at', 'updated_at' # <-- AJOUTER EN CHAMPS
        ]
        read_only_fields = ['author', 'author_matricule']

    def create(self, validated_data):
        sections_data = validated_data.pop('sections', [])
        course = Course.objects.create(**validated_data)
        
        def save_sections(items, parent=None):
            for item in items:
                children = item.pop('children', [])
                sec = Section.objects.create(course=course, parent=parent, **item)
                if children:
                    save_sections(children, parent=sec)

        if sections_data:
            save_sections(sections_data)
        return course


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
