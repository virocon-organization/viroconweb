from django.apps import AppConfig

class ContourConfig(AppConfig):
    name = 'contour'

    def ready(self):
        from . import signals
