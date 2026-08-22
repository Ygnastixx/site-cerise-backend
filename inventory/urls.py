from django.urls import path

from .views import EquipmentListCreateView, EquipmentDetailView

urlpatterns = [
    # Tes routes viendront ici
    path('equipments/', EquipmentListCreateView.as_view(), name='equipment-list-create'),
    path('equipments/<int:pk>/', EquipmentDetailView.as_view(), name='equipment-detail')
]