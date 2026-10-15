"""URL routes for Quizly quiz endpoints."""

from django.urls import path

from quiz_app.api.views import QuizViewSet

quiz_list = QuizViewSet.as_view({"get": "list"})
quiz_detail = QuizViewSet.as_view(
    {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
)

urlpatterns = [
    path("quizzes/", quiz_list, name="quiz-list"),
    path("quizzes/<int:pk>/", quiz_detail, name="quiz-detail"),
]
