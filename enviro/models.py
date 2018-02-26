from django.utils import timezone
from .validators import validate_file_extension
from django.db import models
from django.dispatch import receiver
from user.models import User
import os
from django.core.exceptions import ValidationError

class MeasureFileModel(models.Model):
    """
    Model for a file containing measurement data.

    A MeasureFileModel object holds a measurement file. It is associated to a
    user (owner) and can be shared with other users.
    """

    secondary_user = models.ManyToManyField(User, related_name="secondary",
                                            max_length=50)
    primary_user = models.ForeignKey(User, null=True, related_name="primary")
    title = models.CharField(max_length=50, default="MeasureFile")
    upload_date = models.DateTimeField(default=timezone.now)
    measure_file = models.FileField(validators=[validate_file_extension])

    @staticmethod
    def url_str():
        return "measure_file_model"


# deletes the file which was attached to the MesureFileManager object
@receiver(models.signals.post_delete, sender=MeasureFileModel)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes a file when the corresponding `MediaFile` object is deleted.

    Parameters
    ----------
    sender : ?,
        Description.
    instance : ?,
        Description
    kwargs : ?
        Description
    """

    if instance.measure_file:
        if os.path.isfile(instance.measure_file.path):
            os.remove(instance.measure_file.path)


class ProbabilisticModel(models.Model):
    """
    Model for a multivariate distribution, e.g. a sea state description.

    A ProbabilisticModel object is associated to a user (owner) and can be
    shared with other users. It has a name and can be connected to
    measurement data.
    If a probabilistic model is defined, in addition X DistributionModel objects
    are needed to define the distributions.
    """

    primary_user = models.ForeignKey(User, null=True,
                                     related_name="variables_primary")
    secondary_user = models.ManyToManyField(User,
                                            related_name="variables_secondary")
    upload_date = models.DateTimeField(default=timezone.now)
    collection_name = models.CharField(default='VariablesCollection',
                                       max_length=50)
    measure_file_model = models.ForeignKey(MeasureFileModel,
                                           on_delete=models.CASCADE,
                                           null=True)

    @staticmethod
    def url_str():
        return "probabilistic_model"


class DistributionModel(models.Model):
    """
    Model for the distribution of a single random variable.

    For example the random variable significant wave height, can be defined
    with this model. Its name would be 'significant wave height', its
    symbol 'Hs' and its distribution 'Weibull'. In addition one would need 3
    ParameterModel objects, which define the distributions parameters (scale,
    shape, location).
    """

    DISTRIBUTIONS = (('Normal', 'Normal Distribution'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-Normal'),
                     ('KernelDensity', 'Kernel Density'))
    name = models.CharField(default="peak period", max_length=50)
    symbol = models.CharField(default="Tp", max_length=5)
    distribution = models.CharField(choices=DISTRIBUTIONS, max_length=15)
    probabilistic_model = models.ForeignKey(ProbabilisticModel,
                                            on_delete=models.CASCADE)

    @staticmethod
    def url_str():
        return "distribution"


class ParameterModel(models.Model):
    """
    Model for one parameter of a distribution, e.g. scale.

    The parameter model can either be a constant value, e.g. x0 = 1.5 or
    it can be a function, which describes the parameter's depedency on
    another variable. The two available funtions have 3 parameters each, which
    are represented by x0, x1 and x2.
    """

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
        Validates if the parameter of a distribution has valid values.

        For example a Normal distribution's scale parameter (sigma) must
        be > 0. If this is not the case, a ValidationError is raised.
        """

        # If the parameters are given as constant values
        if self.function == 'None':
            pass
        if self.distribution.distribution == 'Normal':
            if self.name == 'scale' and self.x0 <= 0:
                raise ValidationError(
                    "The Normal distribution's scale parameter, sigma, "
                    "must be > 0.")
        elif self.distribution.distribution == 'Weibull':
            if self.name == 'scale' and self.x0 <= 0:
                raise ValidationError(
                    "The Weibull distribution's scale parameter, lambda, "
                    "must be > 0.")
            elif self.name == 'shape' and self.x0 <= 0:
                raise ValidationError(
                    "The Weibull distribution's shape parameter, k, "
                    "must be > 0.")
        elif self.distribution.distribution == 'Lognormal_2':
            if self.name == 'shape' and self.x0 <= 0:
                raise ValidationError(
                    "The Log-normal's distribution's shape parameter, sigma, "
                    "must be > 0.")

    def __str__(self):
        return "ParameterModel object with: function=%r, x0=%r, x1=%r, x2=%r," \
               " dependency=%r, name=%r" % \
               (self.function, self.x0, self.x1, self.x2,
                self.dependency, self.name)
