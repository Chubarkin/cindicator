from datetime import timedelta
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from django.utils import timezone
from django.urls import reverse
from unittest import mock

from questionnaire.models import Question, Answer

from . import responses
from .serializers import QuestionJsonSerializer
from .views import LoginApiView, AnswerQuestionApiView, QuestionApiView


class TestBaseJsonResponse(TestCase):
    def setUp(self):
        self.response = responses.BaseJsonResponse(data=None, success=True)
        self.response.message = 'Test response'

    @mock.patch('api.responses.BaseJsonResponse._construct_response')
    def test_init(self, _construct_response):
        _construct_response.return_value = {}
        responses.BaseJsonResponse(data=[], success=True)
        self.assertEqual(_construct_response.call_count, 1)

    def test__construct_response(self):
        response = self.response._construct_response('data', True)
        self.assertEqual(response, {'data': 'data', 'message': 'Test response', 'success': True})


class TestValidationErrorJsonResponse(TestCase):
    @mock.patch('api.responses.ValidationErrorJsonResponse._get_error_message')
    def test_init(self, _get_error_message):
        _get_error_message.return_value = ''
        responses.ValidationErrorJsonResponse({})
        self.assertEqual(_get_error_message.call_count, 1)

    @mock.patch('api.responses.ValidationErrorJsonResponse.FIELD_ERROR_MESSAGE_TMPL', '%s — %s')
    @mock.patch('api.responses.ValidationErrorJsonResponse.ERRORS_SPLITTER_TMPL', ', ')
    @mock.patch('api.responses.ValidationErrorJsonResponse.MESSAGES_SPLITTER_TMPL', '; ')
    def test__get_error_message(self):
        errors = {'__all__': ['generic error'], 'test_field': ['test field error']}
        self.response = responses.ValidationErrorJsonResponse({})
        error_message = self.response._get_error_message(errors)
        self.assertIn(error_message, ['generic error; test_field — test field error',
                                      'test field — test_field error; generic error'])


class JsonHandler(TestCase):
    def test_json_handler(self):
        def error_func():
            raise Exception('test exception')

        handled = responses.json_handler(error_func)
        response = handled()
        self.assertIsInstance(response, responses.ServerErrorJsonResponse)


class TestQuestionJsonSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='testuser')
        self.question = Question.objects.create(title='test question', end_time=timezone.now(), real_answer=80)
        self.answer = Answer.objects.create(user=self.user, question=self.question, value=40)

    @mock.patch('api.serializers.QuestionJsonSerializer._get_obj_dict')
    def test_serialize(self, _get_obj_dict):
        data = QuestionJsonSerializer.serialize([self.question])
        self.assertEqual(_get_obj_dict.call_count, 1)
        self.assertIsInstance(data, list)

    @mock.patch('questionnaire.models.Question.get_user_answer')
    @mock.patch('questionnaire.models.Answer.can_edit')
    @mock.patch('questionnaire.models.Question.can_answer')
    def test__get_obj_dict(self, can_answer, can_edit, get_user_answer):
        get_user_answer.return_value = self.answer
        can_edit.return_value = False
        can_answer.return_value = True

        obj_dict = QuestionJsonSerializer._get_obj_dict(self.question)
        self.assertEqual(obj_dict,
                         {
                             'id': self.question.id,
                             'title': self.question.title,
                             'can_edit': False,
                             'end_time': self.question.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                             'user_answer': self.answer.value,
                             'real_answer': self.question.real_answer
                         })

        get_user_answer.return_value = None
        can_edit.return_value = False
        can_answer.return_value = True
        obj_dict = QuestionJsonSerializer._get_obj_dict(self.question)
        self.assertEqual(obj_dict,
                         {
                             'id': self.question.id,
                             'title': self.question.title,
                             'can_edit': True,
                             'end_time': self.question.end_time.strftime("%Y-%m-%d %H:%M:%S"),
                             'user_answer': None,
                             'real_answer': self.question.real_answer
                         })


def add_session(request):
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()


class TestLoginApiView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test', password='testtest')

    def test_post(self):
        request = self.factory.post(reverse('login'),
                                    {'username': 'test',
                                     'password': 'testtest'})
        add_session(request)
        request.user = AnonymousUser()
        response = LoginApiView.as_view()(request)
        self.assertIsInstance(response, responses.SuccessLoginJsonResponse)

        request.user = self.user
        response = LoginApiView.as_view()(request)
        self.assertIsInstance(response, responses.AlreadyLoggedInJsonResponse)

        request = self.factory.post(reverse('login'),
                                    {'username': 'test',
                                     'password': 'wrongpassword'})
        add_session(request)
        request.user = AnonymousUser()
        response = LoginApiView.as_view()(request)
        self.assertIsInstance(response, responses.FailedLoginJsonResponse)


class TestAnswerQuestionApiView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test', password='testtest')
        self.question = Question.objects.create(title='Test title',
                                                end_time=timezone.now() + timedelta(hours=1))

    def test_post(self):
        request = self.factory.post(reverse('answer_question'),
                                    {'question': self.question.id, 'value': 70})
        add_session(request)
        request.user = AnonymousUser()

        response = AnswerQuestionApiView.as_view()(request)
        self.assertIsInstance(response, responses.NotLoggedInJsonResponse)

        request.user = self.user
        response = AnswerQuestionApiView.as_view()(request)
        self.assertIsInstance(response, responses.SuccessJsonResponse)

        request = self.factory.post(reverse('answer_question'),
                                    {'question': self.question.id})
        add_session(request)
        request.user = self.user
        response = AnswerQuestionApiView.as_view()(request)
        self.assertIsInstance(response, responses.ValidationErrorJsonResponse)


class TestQuestionApiView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='test', password='testtest')
        self.question = Question.objects.create(title='Test title',
                                                end_time=timezone.now() + timedelta(hours=1))

    def test_get(self):
        request = self.factory.get(reverse('questions'))
        add_session(request)
        request.user = AnonymousUser()

        response = QuestionApiView.as_view()(request)
        self.assertIsInstance(response, responses.NotLoggedInJsonResponse)

        request.user = self.user
        response = QuestionApiView.as_view()(request)
        self.assertIsInstance(response, responses.SuccessJsonResponse)

        request = self.factory.get(reverse('questions'), {'active': 'True'})
        add_session(request)
        request.user = self.user
        response = QuestionApiView.as_view()(request)
        self.assertIsInstance(response, responses.ValidationErrorJsonResponse)

    @mock.patch('django.utils.timezone.now')
    @mock.patch('questionnaire.forms.QuestionFilterForm.TRUE', 'true')
    def test__get_params(self, now):
        now.return_value = 'now'
        cleaned_data = {'active': 'true', 'has_answer': 'true', 'title': 'TesT'}
        filter_params, exclude_params = QuestionApiView._get_params(cleaned_data, self.user)
        self.assertEqual(filter_params, {
            'end_time__gte': 'now',
            'answer__user': self.user,
            'title__icontains': 'TesT'
        })
        self.assertEqual(exclude_params, {})

        cleaned_data = {'active': 'false', 'has_answer': 'false'}
        filter_params, exclude_params = QuestionApiView._get_params(cleaned_data, self.user)
        self.assertEqual(filter_params, {'end_time__lt': 'now'})
        self.assertEqual(exclude_params, {'answer__user': self.user})

        cleaned_data = {}
        filter_params, exclude_params = QuestionApiView._get_params(cleaned_data, self.user)
        self.assertEqual(filter_params, {})
        self.assertEqual(exclude_params, {})
