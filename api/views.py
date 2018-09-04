from django.contrib.auth import authenticate, login
from django.db.models import Prefetch
from django.views.generic import View
from django.utils import timezone

from questionnaire.forms import AnswerForm, QuestionFilterForm
from questionnaire.models import Answer, Question

from . import responses
from .serializers import QuestionJsonSerializer


class LoginApiView(View):
    @responses.json_handler
    def post(self, request):
        if request.user.is_authenticated:
            return responses.AlreadyLoggedInJsonResponse()

        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return responses.SuccessLoginJsonResponse()

        return responses.FailedLoginJsonResponse()


class AnswerQuestionApiView(View):
    @responses.json_handler
    def post(self, request):
        if not request.user.is_authenticated:
            return responses.NotLoggedInJsonResponse()

        question_id = request.POST.get('question')
        answer = Answer.objects.filter(
            user_id=request.user.id, question_id=question_id).first()

        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.user = request.user
            answer.save()
            return responses.SuccessJsonResponse(
                message='Answer object was created/updated')

        return responses.ValidationErrorJsonResponse(form.errors)


class QuestionApiView(View):
    @responses.json_handler
    def get(self, request):
        if not request.user.is_authenticated:
            return responses.NotLoggedInJsonResponse()

        form = QuestionFilterForm(request.GET)
        if form.is_valid():
            query_params = self._get_params(form.cleaned_data)
            answers = Prefetch(
                'answer_set',
                queryset=Answer.objects.filter(user=request.user),
                to_attr='user_answer')
            questions = Question.objects\
                .prefetch_related(answers).filter(**query_params)
            data = QuestionJsonSerializer.serialize(questions)
            return responses.SuccessJsonResponse(data)

        return responses.ValidationErrorJsonResponse(form.errors)

    @staticmethod
    def _get_params(cleaned_data):
        query_params = {}
        active = cleaned_data.get('active')
        if active:
            now = timezone.now()
            if active == QuestionFilterForm.TRUE:
                query_params['end_time__gte'] = now
            else:
                query_params['end_time__lt'] = now

        has_answer = cleaned_data.get('has_answer')
        if has_answer:
            if has_answer == QuestionFilterForm.TRUE:
                has_answer = True
            else:
                has_answer = False
            query_params['real_answer__isnull'] = not has_answer

        title = cleaned_data.get('title')
        if title:
            query_params['title__icontains'] = title

        return query_params

