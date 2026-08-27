from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from inventory.permissions import InventoryPermission

from .models import Equipment
from .serializers import EquipmentSerializer

# Create your views here.
class EquipmentListCreateView(APIView):
    permission_classes = [IsAuthenticated, InventoryPermission]
    def get(self, request):
        equipments = Equipment.objects.all()
        serializer = EquipmentSerializer(equipments, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = EquipmentSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class EquipmentDetailView(APIView):
    permission_classes = [IsAuthenticated, InventoryPermission]
    def get(self, request, pk):
        equipment = Equipment.objects.get(pk=pk)
        serializer = EquipmentSerializer(equipment)

        return Response(serializer.data)

    def put(self, request, pk):
        equipment = Equipment.objects.get(pk=pk)
        serializer = EquipmentSerializer(equipment, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )