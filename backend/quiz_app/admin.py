"""Admin configuration for Quizly quiz models."""

from django.contrib import admin

from quiz_app.models import Question, Quiz


class QuestionInline(admin.TabularInline):
    """Allow questions to be edited directly inside a quiz."""

    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Configure quiz management in Django admin."""

    list_display = ("id", "title", "user", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("title", "description", "video_url", "user__username")
    inlines = (QuestionInline,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Configure individual question management in Django admin."""

    list_display = ("id", "question_title", "quiz", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("question_title", "answer", "quiz__title")
