from django.urls import re_path

from .views import LoginApiView, AnswerQuestionApiView, QuestionApiView

urlpatterns = [
    re_path(r'^login/?$', LoginApiView.as_view(), name='login'),
    re_path(r'^answer_question/?$', AnswerQuestionApiView.as_view(), name='answer_question'),
    re_path(r'^questions/?$', QuestionApiView.as_view(), name='questions')
]
