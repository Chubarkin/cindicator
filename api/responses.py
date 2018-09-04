from django.http import JsonResponse
from functools import wraps


class BaseJsonResponse(JsonResponse):
    message = None

    def __init__(self, data, success, message=None, *args, **kwargs):
        if data is None:
            data = []

        if message:
            self.message = message

        response = self._construct_response(data, success)
        super().__init__(response, *args, **kwargs)

    def _construct_response(self, data, success):
        return {
            'data': data,
            'message': self.message,
            'success': success
        }


class SuccessJsonResponse(BaseJsonResponse):
    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, success=True, *args, **kwargs)


class ErrorJsonResponse(BaseJsonResponse):
    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, success=False, *args, **kwargs)


class SuccessLoginJsonResponse(SuccessJsonResponse):
    message = 'Successfully logged in'


class AlreadyLoggedInJsonResponse(ErrorJsonResponse):
    message = 'Already logged in'


class FailedLoginJsonResponse(ErrorJsonResponse):
    message = 'Incorrect username or password'


class ServerErrorJsonResponse(ErrorJsonResponse):
    message = 'Server error'


class NotLoggedInJsonResponse(ErrorJsonResponse):
    message = 'User is not logged in'


class ValidationErrorJsonResponse(ErrorJsonResponse):
    FIELD_ERROR_MESSAGE_TMPL = '%s — %s'
    ERRORS_SPLITTER_TMPL = ' ,'
    MESSAGES_SPLITTER_TMPL = '; '

    def __init__(self, form_errors, *args, **kwargs):
        message = self._get_error_message(form_errors)
        super().__init__(message=message, *args, **kwargs)

    def _get_error_message(self, form_errors):
        field_messages = []
        for field, errors in form_errors.items():
            if field == '__all__':
                field_messages.append(self.ERRORS_SPLITTER_TMPL.join(errors))
            else:
                field_messages.append(self.FIELD_ERROR_MESSAGE_TMPL % (
                    field, self.ERRORS_SPLITTER_TMPL.join(errors)))
        return self.MESSAGES_SPLITTER_TMPL.join(field_messages)


def json_handler(view):
    @wraps(view)
    def inner(*args, **kwargs):
        try:
            res = view(*args, **kwargs)
        except Exception:
            return ServerErrorJsonResponse()
        return res
    return inner
