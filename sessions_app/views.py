from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import SessionPermission, IsStaffOrAdminOrReadOnly, IsStaffOrAdmin
from .models import Session
from .serializers import (
    SessionEquipmentSerializer,
    SessionSerializer,
    SessionWriteSerializer,
)


class SessionListCreateView(generics.ListCreateAPIView):
    """GET  /api/sessions/ - liste filtrable (membre / staff / admin)
    POST /api/sessions/ - creation avec reservation de materiel (staff / admin)

    Filtres : ?before_date=AAAA-MM-JJ, ?after_date=AAAA-MM-JJ, ?search=texte
    """

    permission_classes = [SessionPermission]

    def get_serializer_class(self):
        return SessionWriteSerializer if self.request.method == "POST" else SessionSerializer

    def get_queryset(self):
        params = self.request.query_params
        queryset = Session.objects.select_related("course").prefetch_related(
            "equipment_reservations__equipment"
        )

        avant = parse_date(params.get("before_date", "") or "")
        if avant:
            queryset = queryset.filter(date__date__lte=avant)

        apres = parse_date(params.get("after_date", "") or "")
        if apres:
            queryset = queryset.filter(date__date__gte=apres)

        recherche = params.get("search")
        if recherche:
            queryset = queryset.filter(
                Q(theme__icontains=recherche)
                | Q(description__icontains=recherche)
                | Q(location__icontains=recherche)
            )

        if params.get("course_id"):
            queryset = queryset.filter(course_id=params["course_id"])

        return queryset.order_by("-date")


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PUT/PATCH/DELETE /api/sessions/<id>/"""

    permission_classes = [IsStaffOrAdminOrReadOnly]

    def get_queryset(self):
        return Session.objects.select_related("course").prefetch_related(
            "equipment_reservations__equipment"
        )

    def get_serializer_class(self):
        return SessionSerializer if self.request.method == "GET" else SessionWriteSerializer


class ReserveEquipmentView(APIView):
    """POST /api/sessions/<id>/reserve-equipment/ - ajoute ou met a jour une reservation.

    Complete la creation groupee de POST /api/sessions/ pour les ajustements
    materiel apres coup, sans avoir a renvoyer toute la seance.
    """

    permission_classes = [IsStaffOrAdmin]

    def post(self, request, pk):
        session = get_object_or_404(Session, pk=pk)
        serializer = SessionEquipmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        donnees = serializer.validated_data
        session.equipment_reservations.update_or_create(
            equipment=donnees["equipment"],
            defaults={"quantity_reserved": donnees.get("quantity_reserved", 1)},
        )

        session.refresh_from_db()
        return Response(SessionSerializer(session).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """Retire un materiel de la seance (equipment_id en parametre d'URL)."""
        session = get_object_or_404(Session, pk=pk)
        equipment_id = request.query_params.get("equipment_id")

        if not equipment_id:
            return Response(
                {"detail": "Le parametre equipment_id est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session.equipment_reservations.filter(equipment_id=equipment_id).delete()
        session.refresh_from_db()
        return Response(SessionSerializer(session).data, status=status.HTTP_200_OK)


class SessionSectionView(APIView):
    """POST /api/sessions/<id>/sections/ - Associe une section de cours abordée."""
    permission_classes = [IsStaffOrAdmin]

    def post(self, request, pk):
        session = get_object_or_404(Session, pk=pk)
        section_id = request.data.get("section_id")
        
        if not section_id:
            return Response({"detail": "section_id est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)
            
        SessionSection.objects.get_or_create(session=session, section_id=section_id)
        return Response({"detail": "Section ajoutée avec succès."}, status=status.HTTP_200_OK)