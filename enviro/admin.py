from django.contrib import admin
from .models import MeasureFileManager
from .models import ProbabilisticModel, DistributionModel, ParameterModel


# Register your models here.
admin.site.register(MeasureFileManager),
admin.site.register(ProbabilisticModel),
admin.site.register(DistributionModel),
admin.site.register(ParameterModel),
