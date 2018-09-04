from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from unittest import mock

from .models import Question, Answer, Statistics


class TestQuestion(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='testuser')
        self.question = Question.objects.create(title='Test title',
                                                end_time=timezone.now() + timedelta(hours=1))

        self.answer = Answer.objects.create(user=self.user, question=self.question, value=40)

    def test_get_user_answer(self):
        self.question.user_answer = [self.answer]
        answer = self.question.get_user_answer()
        self.assertEqual(self.answer, answer)

        self.question.user_answer = None
        answer = self.question.get_user_answer()
        self.assertIsNone(answer)

        answer = self.question.get_user_answer(self.user)
        self.assertEqual(self.answer, answer)

    def test_can_answer(self):
        self.question.end_time = timezone.now() + timedelta(hours=1)
        self.assertTrue(self.question.can_answer())

        self.question.end_time = timezone.now() - timedelta(hours=1)
        self.assertFalse(self.question.can_answer())


class TestAnswer(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='testuser')
        self.question = Question.objects.create(title='Test title',
                                                end_time=timezone.now() + timedelta(hours=1))

        self.answer = Answer.objects.create(user=self.user, question=self.question, value=40)

    @mock.patch('questionnaire.models.Question.can_answer')
    @mock.patch('questionnaire.models.Answer.MAX_TIME_FOR_EDIT', 1)
    def test_can_edit(self, can_answer):
        self.answer.create_time = None
        self.assertTrue(self.answer.can_edit())

        self.answer.create_time = timezone.now() - timedelta(hours=2)
        self.assertFalse(self.answer.can_edit())

        self.answer.create_time = timezone.now()
        can_answer.return_value = False
        self.assertFalse(self.answer.can_edit())

        can_answer.return_value = True
        self.assertTrue(self.answer.can_edit())


class TestStatistics(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test', password='testuser')
        question = Question.objects.create(title='Test title',
                                           end_time=timezone.now() + timedelta(hours=1))

        self.answer = Answer.objects.create(user=self.user, question=question, value=40)
        Question.objects.create(title='Test title 2',
                                end_time=timezone.now() + timedelta(hours=1))

        self.statistics = Statistics.objects.get_or_create(user=self.user)[0]

    def test_recalculate(self):
        self.statistics.recalculate()
        questions_count = Question.objects.count()
        self.assertEqual(self.statistics.answered_questions + self.statistics.unanswered_questions, questions_count)
        self.assertEqual(self.statistics.answered_questions, self.user.answer_set.count())
