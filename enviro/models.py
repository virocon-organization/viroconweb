from django.utils import timezone
from .validators import validate_file_extension
from django.db import models
from django.dispatch import receiver
from user.models import User
import os
from django.core.exceptions import ValidationError
from decimal import Decimal

class MeasureFileModel(models.Model):
    secondary_user = models.ManyToManyField(User, related_name="secondary", max_length=50)
    primary_user = models.ForeignKey(User, null=True, related_name="primary")
    title = models.CharField(max_length=50, default="MeasureFile")
    upload_date = models.DateTimeField(default=timezone.now)
    measure_file = models.FileField(validators=[validate_file_extension])

    def __str__(self):
        return "measurefiles"


# deletes the file which was attached to the MesureFileManager object
@receiver(models.signals.post_delete, sender=MeasureFileModel)
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
    collection_name = models.CharField(default='VariablesCollection', max_length=50)
    measure_file_model = models.ForeignKey(MeasureFileModel, on_delete=models.CASCADE, null=True)
    def __str__(self):
        return "probabilistic_model"


class DistributionModel(models.Model):
    DISTRIBUTIONS = (('Normal', 'Normal Distribution'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-Normal'), ('KernelDensity', 'Kernel Density'))
    name = models.CharField(default="peak period", max_length=50)
    symbol = models.CharField(default="Tp", max_length=5)
    distribution = models.CharField(choices=DISTRIBUTIONS, max_length=15)
    probabilistic_model = models.ForeignKey(ProbabilisticModel, on_delete=models.CASCADE)

    def __str__(self):
        return "distribution"


class ParameterModel(models.Model):
    FUNCTIONS = ((None, 'None'), ('f1', 'power function'),
                 ('f2', 'exponential'))
    function = models.CharField(choices=FUNCTIONS, max_length=6)
    x0 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10,
                             null=True)
    x1 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10,
                             null=True)
    x2 = models.DecimalField(default=0.000, decimal_places=5, max_digits=10,
                             null=True)
    dependency = models.CharField(default='!', max_length=10)
    # The name attribute can be 'scale', 'shape', or 'location' (see views.py)
    name = models.CharField(default='empty', max_length=10)
    distribution = models.ForeignKey(DistributionModel,
                                     on_delete=models.CASCADE)

    def clean(self):
        """
        Validates that the distribution's parameters have valid values.

        All distribution's parameters are validated. For example a Normal
        distribution's scale parameter (sigma) must be > 0. If this is not
        the case, a ValidationError is raised.
        """

        if self.function == 'None':
            if self.distribution.distribution == 'Normal' and \
                            self.name == 'scale' and \
                            self.x0 <= 0:
                raise ValidationError(
                    "The Normal distribution's scale parameter, sigma, "
                    "must be > 0.")
            elif self.distribution.distribution == 'Weibull' and \
                            self.name == 'scale' and \
                            self.x0 <= 0:
                raise ValidationError(
                    "The Weibull distribution's scale parameter, lambda, "
                    "must be > 0.")
            elif self.distribution.distribution == 'Weibull' and \
                            self.name == 'shape' and \
                            self.x0 <= 0:
                raise ValidationError(
                    "The Weibull distribution's shape parameter, k, "
                    "must be > 0.")
            elif self.distribution.distribution == 'Lognormal_2' and \
                            self.name == 'shape' and \
                            self.x0 <= 0:
                raise ValidationError(
                    "The Log-normal's distribution's shape parameter, sigma, "
                    "must be > 0.")

    def __str__(self):
        return "parameter object with: function=%r, x0=%r, x1=%r, x2=%r," \
               " dependency=%r, name=%r" % \
               (self.function, self.x0, self.x1, self.x2,
                self.dependency, self.name)
