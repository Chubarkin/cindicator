from datetime import timedelta
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .validators import NotEqualValueValidator


class Question(models.Model):
    title = models.TextField('Question')
    real_answer = models.IntegerField(
        'Real answer', null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100), NotEqualValueValidator(50)])
    end_time = models.DateTimeField('End time')

    def get_user_answer(self, user=None):
        if getattr(self, 'user_answer', None):
            return self.user_answer[0]

        user_answer = self.answer_set.filter(user=user).first()
        return user_answer

    def can_answer(self):
        now = timezone.now()
        return self.end_time >= now

    def __str__(self):
        return self.title


class Answer(models.Model):
    MAX_TIME_FOR_EDIT = 1

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.IntegerField(
        'User answer',
        validators=[MinValueValidator(0), MaxValueValidator(100), NotEqualValueValidator(50)])

    create_time = models.DateTimeField('Create time', auto_now_add=True)

    def can_edit(self):
        now = timezone.now()
        if self.create_time:
            return self.create_time + timedelta(hours=self.MAX_TIME_FOR_EDIT) >= now \
                and self.question.can_answer()
        return True

    class Meta:
        unique_together = ('user', 'question')


class Statistics(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    answered_questions = models.IntegerField('Answered questions', default=0)
    unanswered_questions = models.IntegerField('Unanswered questions', default=0)

    def recalculate(self):
        self.answered_questions = self.user.answer_set.count()
        self.unanswered_questions = Question.objects.count() - self.answered_questions
        self.save()
