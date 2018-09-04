from django.apps import AppConfig


class ProjectAppConfig(AppConfig):
    name = 'project'

    def ready(self):
        import project.signals