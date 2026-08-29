from django.urls import path

from . import views

app_name = "sessions_app"

urlpatterns = [
    path("", views.SessionListCreateView.as_view(), name="list-create"),
    path("<int:pk>/", views.SessionDetailView.as_view(), name="detail"),
    path("<int:pk>/reserve-equipment/", views.ReserveEquipmentView.as_view(), name="reserve-equipment"),
]
