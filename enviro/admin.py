from django.contrib import admin
from .models import MeasureFileModel
from .models import ProbabilisticModel, DistributionModel, ParameterModel


# Register your models here.
admin.site.register(MeasureFileModel),
admin.site.register(ProbabilisticModel),
admin.site.register(DistributionModel),
admin.site.register(ParameterModel),
