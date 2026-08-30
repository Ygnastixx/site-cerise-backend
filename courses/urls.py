from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, SectionImageUploadView, SectionViewSet, SectionSchemasView

router = DefaultRouter()
router.register('sections', SectionViewSet, basename='section')
router.register('', CourseViewSet, basename='course')

urlpatterns = [
    path('sections/schemas/', SectionSchemasView.as_view(), name='section-schemas'),
    path('sections/upload-image/', SectionImageUploadView.as_view(), name='section-image-upload'),
    path('', include(router.urls)),
]