from django.urls import path

from . import views

app_name = "studio"

urlpatterns = [
    path("templates/", views.TemplateListCreateView.as_view(), name="template-list"),
    path("templates/<int:pk>/", views.TemplateDetailView.as_view(), name="template-detail"),
    path("generate-poster/", views.GeneratePosterView.as_view(), name="generate-poster"),
    path("generate-slides/", views.GenerateSlidesView.as_view(), name="generate-slides"),
    path("generate-social-post/", views.GenerateSocialPostView.as_view(), name="generate-social-post"),
]
