from django import forms

from .models import Answer


class AnswerForm(forms.ModelForm):
    def clean(self):
        question = self.cleaned_data['question']
        if self.instance and not self.instance.can_edit() \
                or not question.can_answer():
            raise forms.ValidationError(
                'Question can not be answered already')
        return super().clean()

    def save(self, commit=True):
        instance = super().save(commit)
        if not instance.id:
            instance.question = self.cleaned_data['question']
            instance.value = self.cleaned_data['value']
        return instance

    class Meta:
        model = Answer
        fields = ['question', 'value']


class QuestionFilterForm(forms.Form):
    TRUE = 'true'
    FALSE = 'false'
    BOOLEAN_CHOICES = (
        (TRUE, TRUE),
        (FALSE, FALSE)
    )
    active = forms.ChoiceField(required=False, choices=BOOLEAN_CHOICES)
    has_answer = forms.ChoiceField(required=False, choices=BOOLEAN_CHOICES)
    title = forms.CharField(required=False, min_length=2)
