from django.db import transaction
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action

from .models import Course, Section
from .permissions import CoursePermission
from .serializers import CourseDetailSerializer, CourseSerializer, SectionReorderSerializer, SectionSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .schemas import SECTION_SCHEMAS

from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser


class SectionImageUploadView(APIView):
    permission_classes = [CoursePermission]
    parser_classes = [MultiPartParser]

    def post(self, request):
        fichier = request.FILES.get('image')
        if not fichier:
            return Response({"detail": "Le fichier 'image' est obligatoire."}, status=400)

        chemin = default_storage.save(f"sections/{fichier.name}", fichier)
        url = request.build_absolute_uri(default_storage.url(chemin))
        return Response({"url": url}, status=201)
    

class SectionSchemasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        GET /api/courses/sections/schemas/
        Renvoie la configuration des schémas en retirant les fonctions 'extractor'.
        """
        cleaned_schemas = {}
        for code, schema in SECTION_SCHEMAS.items():
            cleaned_schemas[code] = {
                k: v for k, v in schema.items() if k != 'extractor'
            }
        return Response(cleaned_schemas)

class CourseViewSet(viewsets.ModelViewSet):
    permission_classes = [CoursePermission]
    queryset = Course.objects.select_related("author").prefetch_related("sections")

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        is_staff_or_admin = bool(user and (user.is_staff or user.is_superuser))

        params = self.request.query_params
        status_value = params.get("status")
        is_template = params.get("is_template")
        search = params.get("search") or params.get("q")
        author = params.get("author")

        if not is_staff_or_admin:
            # Un simple membre ne voit jamais la corbeille, ni les brouillons
            qs = qs.filter(status=Course.Status.PUBLISHED)
        elif status_value == Course.Status.TRASH:
            # Staff/Admin qui demande explicitement la corbeille
            qs = qs.filter(status=Course.Status.TRASH)
        else:
            # Staff/Admin par défaut : "Actifs" = brouillon + publié, jamais la corbeille
            qs = qs.exclude(status=Course.Status.TRASH)
            if status_value:
                qs = qs.filter(status=status_value)

        if is_template in {"true", "false"}:
            qs = qs.filter(is_template=(is_template == "true"))
        if author:
            qs = qs.filter(author__matricule=author)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        course = self.get_object()
        course.status = Course.Status.PUBLISHED
        course.save(update_fields=["status", "updated_at"])
        return Response(CourseSerializer(course).data)

    @action(detail=True, methods=["patch", "post"])
    def trash(self, request, pk=None):
        course = self.get_object()
        course.status = Course.Status.TRASH
        course.save(update_fields=["status", "updated_at"])
        return Response(CourseSerializer(course).data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        course = self.get_object()
        course.status = Course.Status.DRAFT
        course.save(update_fields=["status", "updated_at"])
        return Response(CourseSerializer(course).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def new_version(self, request, pk=None):
        """Crée une nouvelle version d'un cours (copie ses sections, garde le lien vers l'ancien)."""
        source = self.get_object()
        version = Course.objects.create(
            title=source.title,
            description=source.description,
            status=Course.Status.DRAFT,
            is_template=source.is_template,
            author=request.user,
            previous_version=source,
        )
        mapping = {}
        sections = list(source.sections.order_by("order", "id"))
        for section in sections:
            mapping[section.id] = Section.objects.create(
                course=version, parent=None, title=section.title,
                type=section.type, content=section.content, order=section.order,
            )
        for section in sections:
            if section.parent_id:
                mapping[section.id].parent = mapping[section.parent_id]
                mapping[section.id].save(update_fields=["parent"])
        return Response(CourseDetailSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def duplicate(self, request, pk=None):
        source = self.get_object()
        copy = Course.objects.create(
            title=f"{source.title} (copie)",
            description=source.description,
            status=Course.Status.DRAFT,
            is_template=source.is_template,
            author=request.user,
        )
        mapping = {}
        sections = list(source.sections.order_by("order", "id"))
        # Première passe: créer toutes les sections sans parent.
        for section in sections:
            mapping[section.id] = Section.objects.create(
                course=copy,
                parent=None,
                title=section.title,
                type=section.type,
                content=section.content,
                order=section.order,
            )
        # Deuxième passe: reconstruire les relations parent/enfant.
        for section in sections:
            if section.parent_id:
                mapping[section.id].parent = mapping[section.parent_id]
                mapping[section.id].save(update_fields=["parent"])
        return Response(CourseDetailSerializer(copy).data, status=status.HTTP_201_CREATED)


class SectionViewSet(viewsets.ModelViewSet):
    permission_classes = [CoursePermission]
    serializer_class = SectionSerializer
    queryset = Section.objects.select_related("course", "parent")

    def perform_create(self, serializer):
        serializer.save() # <---

    def get_queryset(self):
        qs = super().get_queryset()
        course_id = self.request.query_params.get("course")
        parent = self.request.query_params.get("parent")
        section_type = self.request.query_params.get("type")
        if course_id:
            qs = qs.filter(course_id=course_id)
        if parent == "null":
            qs = qs.filter(parent__isnull=True)
        elif parent:
            qs = qs.filter(parent_id=parent)
        if section_type:
            qs = qs.filter(type=section_type)
        return qs

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def tree(self, request):
        course_id = request.query_params.get("course")
        if not course_id:
            return Response({"detail": "Le paramètre course est obligatoire."}, status=400)
        sections = list(self.get_queryset().filter(course_id=course_id).order_by("order", "id"))
        by_parent = {}
        for s in sections:
            by_parent.setdefault(s.parent_id, []).append(s)

        def node(s):
            data = SectionSerializer(s).data
            data["children"] = [node(child) for child in by_parent.get(s.id, [])]
            return data

        return Response([node(s) for s in by_parent.get(None, [])])

    @action(detail=False, methods=["post"])
    @transaction.atomic
    def reorder(self, request):
        serializer = SectionReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = [int(item["id"]) for item in serializer.validated_data["items"]]
        sections = {s.id: s for s in Section.objects.filter(id__in=ids)}
        if len(sections) != len(ids):
            return Response({"detail": "Une ou plusieurs sections sont introuvables."}, status=400)
        for item in serializer.validated_data["items"]:
            sections[int(item["id"])].order = int(item["order"])
        Section.objects.bulk_update(sections.values(), ["order"])
        return Response(SectionSerializer(Section.objects.filter(id__in=ids), many=True).data)

