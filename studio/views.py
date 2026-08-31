from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from .permissions import IsAdmin, IsStaffOrAdmin

from .models import SlideTemplate
from .serializers import (
    GeneratePosterSerializer,
    GenerateSlidesSerializer,
    GenerateSocialPostSerializer,
    SlideTemplateSerializer,
)
from .services import construire_affiche, construire_slides, generer_texte_social


class TemplateListCreateView(generics.ListCreateAPIView):
    """GET  /api/studio/templates/ - galerie des gabarits (tout membre connecte)
    POST /api/studio/templates/ - enregistre un gabarit (admin uniquement)
    """

    queryset = SlideTemplate.objects.select_related("created_by")
    serializer_class = SlideTemplateSerializer
    permission_classes = [IsStaffOrAdmin]

    def get_permissions(self):
        # La galerie est consultable par tous ; seul l'admin televerse un gabarit.
        return [IsAdmin()] if self.request.method == "POST" else [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        layout = self.request.query_params.get("layout_type")
        return queryset.filter(layout_type=layout.upper()) if layout else queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/studio/templates/<id>/"""

    queryset = SlideTemplate.objects.select_related("created_by")
    serializer_class = SlideTemplateSerializer

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == "GET" else [IsAdmin()]


class GeneratePosterView(APIView):
    """POST /api/studio/generate-poster/ - donnees d'affiche d'une seance."""

    permission_classes = [IsStaffOrAdmin]

    def post(self, request):
        serializer = GeneratePosterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = serializer.validated_data["session_id"]
        template = serializer.validated_data.get("template_id")

        return Response(construire_affiche(session, template), status=status.HTTP_200_OK)


class GenerateSlidesView(APIView):
    """POST /api/studio/generate-slides/ - structure abstraite des diapositives.

    Ouvert aux membres lorsque le cours est publie, au staff et aux
    administrateurs dans tous les cas.
    """

    permission_classes = [IsStaffOrAdmin]

    def post(self, request):
        serializer = GenerateSlidesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course = serializer.validated_data["course_id"]


        return Response(construire_slides(course), status=status.HTTP_200_OK)


class GenerateSocialPostView(APIView):
    """POST /api/studio/generate-social-post/ - texte d'annonce redige par IA."""

    permission_classes = [IsStaffOrAdmin]

    def post(self, request):
        serializer = GenerateSocialPostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = serializer.validated_data["session_id"]
        texte, source = generer_texte_social(session)

        return Response({"generated_text": texte, "source": source}, status=status.HTTP_200_OK)
