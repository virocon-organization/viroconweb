from django.apps import AppConfig

class EnviroConfig(AppConfig):
    name = 'enviro'

    def ready(self):
        from . import signals