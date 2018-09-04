from django.core.validators import BaseValidator


class NotEqualValueValidator(BaseValidator):
    message = 'This value can not be %(value)s'

    def compare(self, a, b):
        return a == b
