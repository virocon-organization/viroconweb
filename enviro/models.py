from django.utils import timezone
from .validators import validate_file_extension
from django.db import models
from django.dispatch import receiver
from django.contrib.auth.models import User
import os


class MeasureFileManager(models.Model):
    secondary_user = models.ManyToManyField(User, related_name="secondary", max_length=20)
    primary_user = models.ForeignKey(User, null=True, related_name="primary")
    title = models.CharField(max_length=20, default="MeasureFile")
    upload_date = models.DateTimeField(default=timezone.now)
    measure_file = models.FileField(validators=[validate_file_extension])

    def __str__(self):
        return "measurefiles"


# deletes the file which was attached to the MesureFileManager object
@receiver(models.signals.post_delete, sender=MeasureFileManager)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from filesystem when corresponding `MediaFile` object is deleted.
    :param sender: 
    :param instance:       one item form the MeasureFile database. 
    :param kwargs: 
    :return: 
    """
    if instance.measure_file:
        if os.path.isfile(instance.measure_file.path):
            os.remove(instance.measure_file.path)


class ProbabilisticModel(models.Model):
    primary_user = models.ForeignKey(User, null=True, related_name="variables_primary")
    secondary_user = models.ManyToManyField(User, related_name="variables_secondary")
    upload_date = models.DateTimeField(default=timezone.now)
    collection_name = models.CharField(default='VariablesCollection', max_length=25)

    def __str__(self):
        return "probabilistic_model"


class DistributionModel(models.Model):
    DISTRIBUTIONS = (('Normal', 'Normal Distribution'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-Normal'), ('KernelDensity', 'Kernel Density'))
    name = models.CharField(default="peak period", max_length=25)
    symbol = models.CharField(default="p", max_length=5)
    distribution = models.CharField(choices=DISTRIBUTIONS, max_length=15)
    probabilistic_model = models.ForeignKey(ProbabilisticModel, on_delete=models.CASCADE)

    def __str__(self):
        return "distribution"


class ParameterModel(models.Model):
    FUNCTIONS = ((None, 'None'), ('polynomial', 'polynomial'), ('exponential', 'exponential'), ('exppoly', 'exppoly'))
    function = models.CharField(choices=FUNCTIONS, max_length=6)
    x0 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10, null=True)
    x1 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10, null=True)
    x2 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10, null=True)
    dependency = models.CharField(default='!', max_length=10)
    name = models.CharField(default='empty', max_length=10)
    distribution = models.ForeignKey(DistributionModel, on_delete=models.CASCADE)

    def __str__(self):
        return "parameter"
