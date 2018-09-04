from django.apps import AppConfig


class CindicatorAppConfig(AppConfig):
    name = 'cindicator'

    def ready(self):
        import cindicator.signals