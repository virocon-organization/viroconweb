"""
The interface between this package (viroconweb) and the package virocomcom,
which handles the statistical computations
"""
import pandas as pd

from .models import MeasureFileModel, ParameterModel, DistributionModel, \
    ProbabilisticModel
from .settings import MAX_COMPUTING_TIME

from viroconcom.fitting import Fit
from viroconcom.contours import IFormContour, HighestDensityContour
from viroconcom.params import ConstantParam, FunctionParam
from viroconcom.distributions import (NormalDistribution,
                                      LognormalDistribution,
                                      WeibullDistribution,
                                      KernelDensityDistribution,
                                      MultivariateDistribution)


class ComputeInterface:
    @staticmethod
    def fit_curves(mfm_item: MeasureFileModel, fit_settings, var_number):
        """
        Interface to fit a probabilistic model to a measurement file with
        the viroconcom package.

        Parameters
        ----------
        mfm_item : MeasureFileModel,
            Contains the measured data, which should be evaluated.
        fit_settings : ?,
            The settings how the fit should be performed. Here, the
            distribution, which should be fitted to the data, is specified.
        var_number : int,
            Number of random variables that the probabilistic model should have.

        Returns
        -------
        fit : Fit,
            The fit contains the probabilistic model, which was fitted to the
            measurement data, as well as data describing how well the fit worked.
        """
        data_path = mfm_item.measure_file.url
        if data_path[0] == '/':
            data_path = data_path[1:]
        data = pd.read_csv(data_path, sep=';', header=1).as_matrix()
        dists = []
        dates = []
        for i in range(0, var_number):
            dates.append(data[:, i].tolist())
            if i == 0:
                dists.append(
                    {'name': fit_settings['distribution_%s' % i],
                     'number_of_intervals': None,
                     'width_of_intervals': float(
                         fit_settings['width_of_intervals_%s' % i]),
                     'dependency': [None, None, None]
                     })
            elif i == (var_number - 1):  # last variable
                dists.append(
                    {'name': fit_settings['distribution_%s' % i],
                     'number_of_intervals': None,
                     'width_of_intervals': None,
                     'dependency': [
                         adjust(fit_settings['shape_dependency_%s' % i][0]),
                         adjust(fit_settings['location_dependency_%s' % i][0]),
                         adjust(fit_settings['scale_dependency_%s' % i][0])],
                     'functions': [
                         adjust(fit_settings['shape_dependency_%s' % i][1:]),
                         adjust(fit_settings['location_dependency_%s' % i][1:]),
                         adjust(fit_settings['scale_dependency_%s' % i][1:])]
                     })
            else:
                dists.append(
                    {'name': fit_settings['distribution_%s' % i],
                     'number_of_intervals': None,
                     'width_of_intervals': float(
                         fit_settings['width_of_intervals_%s' % i]),
                     'dependency': [
                         adjust(fit_settings['shape_dependency_%s' % i][0]),
                         adjust(fit_settings['location_dependency_%s' % i][0]),
                         adjust(fit_settings['scale_dependency_%s' % i][0])],
                     'functions': [
                         adjust(fit_settings['shape_dependency_%s' % i][1:]),
                         adjust(fit_settings['location_dependency_%s' % i][1:]),
                         adjust(fit_settings['scale_dependency_%s' % i][1:])]
                     })
            # Delete unused parameters
            if dists[i].get('name') == 'Lognormal_2' and i > 0:
                dists[i].get('dependency')[1] = None
                dists[i].get('functions')[1] = None
            elif dists[i].get('name') == 'Normal' and i > 0:
                dists[i].get('dependency')[0] = None
                dists[i].get('functions')[0] = None

        fit = Fit(dates, dists, timeout=MAX_COMPUTING_TIME)
        return fit

    @staticmethod
    def iform(probabilistic_model: ProbabilisticModel, return_period, state_duration,
              n_points):
        """
        Interface to viroconcom to compute an IFORM contour.

        Parameters
        ----------
        probabilistic_model : ProbabilisticModel,
            The probabilistic model, i.e. the joint distribution function,
            which should be evaluated.
        return_period : float,
            The return period of the contour in years.
        state_duration : float,
            The sea state's or more general the environmental state's duration
            in hours.
        n_points : int,
            Number of points along the contour that should be calculated.

        Returns
        -------
        contour_coordinates : list of list of numpy.ndarray,
            Contains the coordinates of points on the contour.
            The outer list contains can hold multiple contour paths if the
            distribution is multimodal. The inner list contains multiple
            numpy arrays of the same length, one per dimension.
            The values of the arrays are the coordinates in the corresponding
            dimension.
        """
        mul_dist = setup_mul_dist(probabilistic_model)
        contour = IFormContour(mul_var_distribution=mul_dist,
                               return_period=return_period,
                               state_duration=state_duration,
                               n_points=n_points,
                               timeout=MAX_COMPUTING_TIME)
        contour_coordinates = contour.coordinates
        return contour_coordinates

    @staticmethod
    def hdc(probabilistic_model: ProbabilisticModel, return_period,
            state_duration, limits, deltas):
        """
        Interface to viroconcom to compute an highest density contour (HDC).

        Parameters
        ----------
        probabilistic_model : ProbabilisticModel,
            The probabilistic model, i.e. the joint distribution function,
            which should be evaluated.
        return_period : float,
            The return period of the contour in years.
        state_duration : float,
            The sea state's or more general the environmental state's duration
            in hours.
        limits : list of tuple,
            One 2-element tuple per dimension in mul_var_distribution,
            containing min and max limits for calculation ((min, max)).
            The smaller value is always assumed minimum.
        deltas : float or list of float,
            The grid cell size used for the calculation.
            If a single float is supplied it is used for all dimensions.
            If a list of float is supplied it has to be of the same length
            as there are dimensions in mul_var_dist.

        Returns
        -------
        contour_coordinates : list of list of numpy.ndarray,
            Contains the coordinates of points on the contour.
            The outer list contains can hold multiple contour paths if the
            distribution is multimodal. The inner list contains multiple
            numpy arrays of the same length, one per dimension.
            The values of the arrays are the coordinates in the corresponding
            dimension.
        """
        mul_dist = setup_mul_dist(probabilistic_model)
        contour = HighestDensityContour(mul_var_distribution=mul_dist,
                                        return_period=return_period,
                                        state_duration=state_duration,
                                        limits=limits,
                                        deltas=deltas,
                                        timeout=MAX_COMPUTING_TIME)
        contour_coordinates = contour.coordinates
        return contour_coordinates


def adjust(var):
    """
    Adjusts the variables types of values, which correspond to viroconweb's
    models, which are associated to a database, to variable types compatible
    with the viroconcom package.
    """
    if var == 'None' or var == '!':
        return None
    elif var.isdigit():
        return int(var)
    else:
        return var


def setup_mul_dist(probabilistic_model: ProbabilisticModel):
    """
    Generates a MultiVariateDistribution from a ProbabilisticModel.

    MultiVariateDistribution objects are used to perform the statistical
    computations in the viroconcom package. ProbabilisticModel objects are used
    in the viroconweb package to be saved in the data base.

    Parameters
    ----------
    probabilistic_model : ProbabilisticModel,
        The probabilistic model, which should be converted.

    Returns
    -------
    mutivar_distribution : MultivariateDistribution,
        The object, which can be used in the viroconcom package.

    """
    distributions_model = DistributionModel.objects.filter(
        probabilistic_model=probabilistic_model)
    distributions = []
    dependencies = []

    for dist in distributions_model:
        dependency = []
        parameters = []
        parameters_model = ParameterModel.objects.filter(distribution=dist)
        for param in parameters_model:
            dependency.append(adjust(param.dependency))

            if adjust(param.function) is not None:
                parameters.append(
                    FunctionParam(float(param.x0), float(param.x1),
                                  float(param.x2), param.function))
            else:
                parameters.append(ConstantParam(float(param.x0)))

        dependencies.append(dependency)

        if dist.distribution == 'Normal':
            distributions.append(NormalDistribution(*parameters))
        elif dist.distribution == 'Weibull':
            distributions.append(WeibullDistribution(*parameters))
        elif dist.distribution == 'Lognormal_2':
            distributions.append(
                LognormalDistribution(sigma=parameters[0], mu=parameters[2]))
        elif dist.distribution == 'KernelDensity':
            distributions.append(KernelDensityDistribution(*parameters))
        else:
            raise KeyError(
                '{} is not a matching distribution'.format(dist.distribution))

    mutivar_distribution = MultivariateDistribution(distributions, dependencies)
    return mutivar_distribution
