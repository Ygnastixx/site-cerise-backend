from django.urls import path

urlpatterns = [
    # Tes routes viendront ici
]

from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, SectionViewSet

router = DefaultRouter()
router.register(r"sections", SectionViewSet, basename="section")
router.register(r"", CourseViewSet, basename="course")

urlpatterns = router.urls
