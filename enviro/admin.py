from django.contrib import admin
from .models import MeasureFileModel
from .models import ProbabilisticModel, DistributionModel, ParameterModel, \
    EnvironmentalContour, AdditionalContourOption, ContourPath, \
    ExtremeEnvDesignCondition, EEDCScalar


# Register your models here.
admin.site.register(MeasureFileModel),
admin.site.register(ProbabilisticModel),
admin.site.register(DistributionModel),
admin.site.register(ParameterModel),
admin.site.register(EnvironmentalContour),
admin.site.register(AdditionalContourOption),
admin.site.register(ContourPath),
admin.site.register(ExtremeEnvDesignCondition),
admin.site.register(EEDCScalar)
