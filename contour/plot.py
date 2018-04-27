import pandas as pd
import numpy as np
import os
import tempfile
import warnings

from scipy.stats import weibull_min
from scipy.stats import lognorm
from scipy.stats import norm
from django.template.loader import get_template
from subprocess import Popen, PIPE
from io import BytesIO, StringIO
from django.core.files.base import ContentFile
from urllib import request
from virocon.settings import USE_S3


# There is a problem with using matplotlib on a server (with Heroku and Travis).
#
# The standard solution to fix it is to use:
#   import matplotlib
#   matplotlib.use('Agg')
#   import matplotlib.pyplot as plt
# see https://stackoverflow.com/questions/41319082/import-matplotlib-failing-
# with-no-module-named-tkinter-on-heroku
#
# However this does not work. Consequently we use another solution, which is
# inspired by https://stackoverflow.com/questions/3285193/how-to-switch-backends
# -in-matplotlib-python
import matplotlib

all_backends = matplotlib.rcsetup.all_backends
backend_worked = False
for gui in all_backends:
    try:
        print("Testing", gui)
        matplotlib.use(gui, warn=False, force=True)
        from matplotlib import pyplot as plt

        backend_worked = True
        break
    except:
        continue
print("Using", matplotlib.get_backend())
if backend_worked == False or matplotlib.get_backend() == 'TkAgg':
    from matplotlib import pyplot as plt

    plt.switch_backend('agg')
    print("Switched backend and now using", matplotlib.get_backend())

from mpl_toolkits.mplot3d import axes3d, Axes3D # Needed for projection='3d'
from descartes import PolygonPatch
from .plot_generic import alpha_shape
from .plot_generic import convert_ndarray_list_to_multipoint

from . import settings

from .models import ProbabilisticModel, DistributionModel, ParameterModel, \
    AdditionalContourOption, PlottedFigure
from .compute_interface import setup_mul_dist


def plot_pdf_with_raw_data(main_index, parent_index, low_index, shape, loc,
                           scale, distribution_type, dist_points, interval,
                           var_name, symbol_parent_var, directory,
                           probabilistic_model):
    """
    The function creates an image which shows a certain fit of a distribution.
    Parameters
    ----------
    main_index : int
          The index of the current dimension (distribution). The index is used to recognise the image later.
    parent_index : int
        The index of the variable on which the conditional is based (when no condition: None).
    low_index : int
         The index of the interval. (needed to recognize the images later)
    shape : float
        The value of the shape parameter.
    loc : float
        The value of the loc parameter. (location)
    scale : float
        The value of the scale parameter.
    distribution_type: str
        Type / name of the distribution, must be "Normal", "Weibull" or "Lognormal"
    dist_points: list of floats
       The dates for the histogram.
    interval : list of floats
        The list contains the interval of the plotted distribution.
    var_name : str
        The name of a single variable of the probabilistic model.
    symbol_parent_var : str
        Symbol of the variable on which the conditional variable is based.
    directory : str
        The directory where the figure should be saved
    probabilistic_model : ProbabilisticModel
        Probabilistic model which has the particular pdf.
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)

    if distribution_type == 'Normal':
        x = np.linspace(norm.ppf(0.0001, loc, scale),
                        norm.ppf(0.9999, loc, scale), 100)
        y = norm.pdf(x, loc, scale)
        text = distribution_type + ', ' + 'mu: ' + str(format(loc, '.3f')) + \
               ' sigma: ' + str(format(scale, '.3f'))
    elif distribution_type == 'Weibull':
        x = np.linspace(weibull_min.ppf(0.0001, shape, loc, scale),
                        weibull_min.ppf(0.9999, shape, loc, scale), 100)
        y = weibull_min.pdf(x, shape, loc, scale)
        text = distribution_type + ', ' + 'shape: ' + \
               str(format(shape, '.3f')) + ' loc: ' + str(
            format(loc, '.3f')) + ' scale: ' + str(format(scale, '.3f'))
    elif distribution_type == 'Lognormal':
        # This makes no sense
        # The scale parameter for python's lognorm  funciton is e^\mu.
        # However in the django data base we save mu as the scale parameter. Maybe we save the
        # mu parameter in the db.
        # scale = np.exp(scale)
        print('scale plot value: {}----------------------'.format(scale))
        x = np.linspace(lognorm.ppf(0.0001, shape, scale=scale),
                        lognorm.ppf(0.9999, shape, scale=scale), 100)
        y = lognorm.pdf(x, shape, scale=scale)

        # The plot function works with the scale parameter but the user interface
        # works with the mu value. However the scale value must be adjusted.
        print('scale adjusted to mu: {} --------------'.format(np.log(scale)))
        text = distribution_type + ', ' + 'sigma: ' + \
               str(format(shape, '.3f')) + ' mu: ' + \
               str(format(np.log(scale), '.3f'))
    else:
        raise KeyError('No function match - {}'.format(distribution_type))

    text = text + ' ('
    if symbol_parent_var:
        text = text + str(format(interval[0], '.3f')) + '≤' + \
               symbol_parent_var + '<' + str(
            format(interval[1], '.3f')) + ', '
    text = text + 'n=' + str(len(dist_points)) + ')'

    ax.plot(x, y, 'r-', lw=5, alpha=0.6, label=distribution_type)
    n_intervals_histogram = int(round(len(dist_points) / 50.0))
    if n_intervals_histogram > 100:
        n_intervals_histogram = 100
    if n_intervals_histogram < 10:
        n_intervals_histogram = 10

    ax.hist(dist_points, n_intervals_histogram, normed=True,
            histtype='stepfilled', alpha=0.9, color='#54889c')
    ax.grid(True)

    plt.title(text)
    plt.xlabel(var_name)
    plt.ylabel('probability density [-]')
    main_index_2_digits = str(main_index).zfill(2)
    parent_index_2_digits = str(parent_index).zfill(2)
    low_index_2_digits = str(low_index).zfill(2)

    # The convention for image name is like this: 'fit_01_00_02.png' means
    # a plot of the second variable (01) which is conditional on the first
    # variable (00) and this is the third (02) fit
    # For the following block thanks to: https://stackoverflow.com/questions/
    # 20580179/saving-a-matplotlib-graph-as-an-image-field-in-database
    f = BytesIO()
    plt.savefig(f, bbox_inches='tight')
    plt.close(fig)
    content_file = ContentFile(f.getvalue())
    plotted_figure = PlottedFigure(probabilistic_model=probabilistic_model)
    file_name = 'fit_' + main_index_2_digits + '_' + parent_index_2_digits + \
                '_' + low_index_2_digits + '.png'
    plotted_figure.image.save(file_name, content_file)
    plotted_figure.save()

    return


def plot_parameter_fit_overview(main_index, var_name, var_symbol, para_name,
                                param_at, param_values, fit_func,
                                directory, dist_name,
                                probabilistic_model):
    """
    Plots an image which shows the fit of a function.

    Parameters
    ----------
    main_index : int
        Index of the related distribution.
    var_name : str
        Name of a multivariate distribution.
    var_symbol : str
          Symbol of a multivariate distribution.
    para_name : str
        Parameter name like shape, location, scale.
    param_at : list of floats
         The list contains the x-values of a fitted function for a parameter e.g. shape, loc or scale.
    param_values : list of floats
        The list contains the y-values of a fitted function for a parameter e.g. shape, loc or scale.
    fit_func : FunctionParam
        The fit function e.g. power function, exponential
    directory : str
        The directory where the figure will be saved.
    dist_name : str
        Name of the distribution, e.g. "Lognormal".
    probabilistic_model : ProbabilisticModel
        Probabilistic model that was created based on this fit.
    """
    if dist_name == 'Weibull':
        if para_name == 'shape':
            y_text = 'k (shape)'
        elif para_name == 'loc':
            y_text = 'θ (location)'
        elif para_name == 'scale':
            y_text = 'λ (scale)'
    elif dist_name == 'Lognormal':
        if para_name == 'shape':
            y_text = 'σ (sigma)'
        elif para_name == 'scale':
            y_text = 'μ (mu)'
    elif dist_name == 'Normal':
        if para_name == 'shape':
            return
        elif para_name == 'loc':
            y_text = 'μ (mean)'
        elif para_name == 'scale':
            y_text = 'σ (standard deviation)'
    else:
        y_text = para_name

    fig = plt.figure()
    ax = fig.add_subplot(111)
    x = np.linspace(min(param_at) - 2, max(param_at) + 2, 100)
    y = []
    for x1 in x:
        y.append(fit_func(x1))
    ax.plot(x, y, color='#54889c')

    ax.scatter(param_at, param_values, color='#9C373A')
    ax.grid(True)
    plt.title('Variable: ' + var_name)
    plt.ylabel(y_text)
    plt.xlabel(var_name)

    # For the following block thanks to: https://stackoverflow.com/questions/
    # 20580179/saving-a-matplotlib-graph-as-an-image-field-in-database
    f = BytesIO()
    plt.savefig(f, bbox_inches='tight')
    plt.close(fig)
    content_file = ContentFile(f.getvalue())
    plotted_figure = PlottedFigure(probabilistic_model=probabilistic_model)
    file_name = 'fit_' + str(main_index) + para_name + '.png'
    plotted_figure.image.save(file_name, content_file)
    plotted_figure.save()



def plot_var_dependent(param_name,
                       param_index,
                       main_index,
                       var_name,
                       var_symbols,
                       param,
                       directory,
                       dist_name,
                       fit_inspection_data,
                       fit,
                       probabilistic_model):
    """
    Plots the fitted distribution for each interval and the resulting fit function for a parameter like shape, loc or
    scale.

    Parameters
    ----------
    param_name : str
        The name of the parameter (e.g. shape, loc or scale).
    param_index : int
        The index represents a parameter of the three possible parameter shape, loc, scale.
        (0 = shape, 1 = loc, 2 = scale)
    main_index : int
        The dimension of the distribution.
    var_name: str
        Name of the distribution.
    var_symbols : list of str
        The symbols of the distribution.
    param : FunctionParam
        The used function for the fit (e.g. exponential, power function)
    directory : str
        Path to the directory where the images will be stored.
    dist_name : str
        Name of the Distributin (e.g. Weibull, Normal, Log-Normal)
    fit_inspection_data : FitInspectionData
        Information for plotting the fits of a single dimension.
    fit : Fit
        Holds data and information about the fit.
    probabilistic_model : ProbabilisticModel
        Probabilistic model that was created based on that fit.
    """
    param_at, param_value = fit_inspection_data.get_dependent_param_points(param_name)
    plot_parameter_fit_overview(main_index, var_name, var_symbols[main_index],
                                param_name, param_at, param_value,
                                param, directory, dist_name, probabilistic_model)
    for j in range(len(param_at)):
        basic_fit = fit_inspection_data.get_basic_fit(param_name, j)
        interval_limits = calculate_intervals(param_at, main_index, j)
        parent_index = fit.mul_var_dist.dependencies[main_index][param_index]
        symbol_parent_var = None
        if parent_index is not None:
            symbol_parent_var = var_symbols[parent_index]
        plot_pdf_with_raw_data(main_index, parent_index, j, basic_fit.shape,
                               basic_fit.loc, basic_fit.scale,
                               fit.mul_var_dist.distributions[main_index].name,
                               basic_fit.samples, interval_limits,
                               var_symbols[main_index], symbol_parent_var,
                               directory, probabilistic_model)


def plot_var_independent(param_name,
                         param_index,
                         main_index,
                         var_symbols,
                         directory,
                         fit_inspection_data,
                         fit,
                         probabilistic_model):
    """
    Plots the fitted distribution of a independent parameter (e.g. shape, loc or scale).

    Parameters
    ----------
    param_name : str
        The name of the parameter (e.g. shape, loc or scale).
    param_index : int
        The index represents a parameter of the three possible parameter shape, loc, scale.
        (0 = shape, 1 = loc, 2 = scale)
    main_index : int
        The dimension of the distribution.
    var_symbols : list of str
        The symbols of the distribution.
    directory : str
        Path to the directory where the images will be stored.
    fit_inspection_data : FitInspectionData
        Information for plotting the fits of a single dimension.
    fit : Fit
        Holds data and information about the fit.
    probabilistic_model : ProbabilisticModel
        Probabilistic model that was created based on that fit.
    """
    basic_fit = fit_inspection_data.get_basic_fit(param_name, 0)
    interval_limits = []
    parent_index = fit.mul_var_dist.dependencies[main_index][param_index]
    symbol_parent_var = None
    if parent_index is not None:
        symbol_parent_var = var_symbols[parent_index]
    plot_pdf_with_raw_data(main_index,
                           parent_index,
                           0,
                           basic_fit.shape,
                           basic_fit.loc,
                           basic_fit.scale,
                           fit.mul_var_dist.distributions[main_index].name,
                           basic_fit.samples,
                           interval_limits,
                           var_symbols[main_index],
                           symbol_parent_var,
                           directory,
                           probabilistic_model)


def plot_fit(fit, var_names, var_symbols, directory, probabilistic_model):
    """
    Visualize a fit generated by the virconcom package.

    Parameters
    ----------
    fit : Fit
        Holds data and information about the fit.
    var_names : list of str
        The list contains the names of distributions
    var_symbols : list of str
        The symbols of the distribution.
    directory : str
        Path to the directory where the images will be stored.
    probabilistic_model : ProbabilisticModel
       Model for a multivariate distribution, e.g. a sea state description.

    """
    directory = directory + '/' + str(probabilistic_model.pk)
    if not os.path.exists(directory):
        os.makedirs(directory)

    for i, fit_inspection_data in enumerate(fit.multiple_fit_inspection_data):
        # Shape
        if fit_inspection_data.shape_at is not None:
            plot_var_dependent(
                'shape', 0, i, var_names[i], var_symbols,
                fit.mul_var_dist.distributions[i].shape, directory,
                fit.mul_var_dist.distributions[i].name,
                fit_inspection_data, fit, probabilistic_model
            )
        else:
            plot_var_independent(
                'shape', 0, i, var_symbols, directory, fit_inspection_data,
                fit, probabilistic_model
            )
        # Loccation
        if fit_inspection_data.loc_at is not None:
            plot_var_dependent(
                'loc', 1, i, var_names[i], var_symbols,
                fit.mul_var_dist.distributions[i].loc, directory,
                fit.mul_var_dist.distributions[i].name,
                fit_inspection_data, fit, probabilistic_model
            )
        else:
            plot_var_independent('loc', 1, i, var_symbols, directory,
                                 fit_inspection_data, fit, probabilistic_model
                                 )
        # Scale
        if fit_inspection_data.scale_at is not None:
            plot_var_dependent('scale', 2, i, var_names[i], var_symbols,
                               fit.mul_var_dist.distributions[i].scale,
                               directory,
                               fit.mul_var_dist.distributions[i].name,
                               fit_inspection_data, fit, probabilistic_model
                               )
        else:
            plot_var_independent('scale', 2, i, var_symbols, directory,
                                 fit_inspection_data, fit, probabilistic_model
                                 )


def calculate_intervals(interval_centers, dimension_index, interval_index):
    """
    Calculates the width of a certain interval.

    Parameters
    ----------
    interval_centers : list of floats
        The intervals of the fit.
    dimension_index : int
        The index of the dimension.
    interval_index : int
        The index of the interval in the current dimension.

    """
    if dimension_index == 0 or len(interval_centers) < 2:
        interval_limits = [min(interval_centers),
                           max(interval_centers)]
    else:
        # Calculate  the interval width assuming constant
        # interval width.
        interval_width = interval_centers[1] - interval_centers[0]
        interval_limits = [interval_centers[interval_index] - 0.5 * interval_width,
                           interval_centers[interval_index] + 0.5 * interval_width]
    return interval_limits



def is_legit_distribution_parameter_index(distribution_name, index):
    """
    Check if the distribution has this kind of parameter index

    Parameters
    ----------
    distribution_name : str
        The name of a Distribution must be 'Normal', 'Lognormal' or 'Weibull'.
    index : int
        The index represents a parameter of the three possible parameter shape, loc, scale.
        (0 = shape, 1 = loc, 2 = scale)
    """
    if distribution_name == 'Normal':
        if index == 0:
            return False
        else:
            return True
    elif distribution_name == 'Weibull':
        return True
    elif distribution_name == 'Lognormal':
        if index == 1:
            return False
        else:
            return True
    else:
        warnings.warn("The distribution name you used to call "
                      "is_legit_distribution_parameter_index() "
                      "is not supported")
        return False


def plot_contour(contour_coordinates, user, environmental_contour, var_names):
    """
    The function plots a png image of a contour.

    Parameters
    ----------
    contour_coordinates : list of floats
        Data points of the contour.
    user : str
        Who gives the contour calculation order.
    environmental_contour : EnvironmentalContour
        The model object contains all information about a environmental contour.
    var_names: list of str
      Name of the variables of the probabilistic model
    """

    probabilistic_model = environmental_contour.probabilistic_model

    path = settings.PATH_MEDIA + settings.PATH_USER_GENERATED + str(user)
    if not os.path.exists(path):
        os.makedirs(path)

    fig = plt.figure()

    if len(contour_coordinates[0]) == 2:
        ax = fig.add_subplot(111)

        # Plot raw data
        if (probabilistic_model.measure_file_model):
            data_path = probabilistic_model.measure_file_model.measure_file.url
            if data_path[0] == '/':
                data_path = data_path[1:]
            data = pd.read_csv(data_path, sep=';', header=0).as_matrix()
            ax.scatter(data[:, 0], data[:, 1], s=5, c='k',
                       label='measured/simulated data')

        # Plot contour
        alpha = .1
        for i in range(len(contour_coordinates)):
            ax.scatter(contour_coordinates[i][0], contour_coordinates[i][1], s=15, c='b',
                       label='extreme env. design condition')
            concave_hull, edge_points = alpha_shape(
                convert_ndarray_list_to_multipoint(contour_coordinates[i]), alpha=alpha)

            patch_design_region = PolygonPatch(
                concave_hull, fc='#999999', linestyle='None', fill=True,
                zorder=-2, label='design region')
            patch_environmental_contour = PolygonPatch(
                concave_hull, ec='b', fill=False, zorder=-1,
                label='environmental contour')
            ax.add_patch(patch_design_region)
            ax.add_patch(patch_environmental_contour)

        plt.legend(loc='lower right')
        plt.xlabel('{}'.format(var_names[0]))
        plt.ylabel('{}'.format(var_names[1]))
    elif len(contour_coordinates[0]) == 3:
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.scatter(contour_coordinates[0][0], contour_coordinates[0][1],
                   contour_coordinates[0][2], marker='o', c='r')
        ax.set_xlabel('{}'.format(var_names[0]))
        ax.set_ylabel('{}'.format(var_names[1]))
        ax.set_zlabel('{}'.format(var_names[2]))
    else:
        ax = fig.add_subplot(111)
        plt.figtext(0.5, 0.5, '4-Dim plot is not supported')
        warnings.warn("4-Dim plot or higher is not supported",
                      DeprecationWarning, stacklevel=2)

    ax.grid(True)

    directory = settings.PATH_MEDIA + settings.PATH_USER_GENERATED + user + \
        '/contour/' + str(environmental_contour.pk) + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)
    # For the following block thanks to: https://stackoverflow.com/questions/
    # 20580179/saving-a-matplotlib-graph-as-an-image-field-in-database
    f = BytesIO()
    plt.savefig(f, bbox_inches='tight')
    plt.close(fig)
    content_file = ContentFile(f.getvalue())
    plotted_figure = PlottedFigure(environmental_contour=environmental_contour)
    file_name = 'contour.png'
    plotted_figure.image.save(file_name, content_file)
    plotted_figure.save()


def plot_data_set_as_scatter(user, measure_file_model, var_names):
    fig = plt.figure(figsize=(7.5, 5.5*(len(var_names)-1)))
    data_path = measure_file_model.measure_file.url
    if data_path[0] == '/':
        data_path = data_path[1:]

    # Number of lines of th header is correctly set to 0! Originally it was 1,
    # which caused a bug since the first data row was ignored, see issue #20.
    data = pd.read_csv(data_path, sep=';', header=0).as_matrix()

    for i in range(len(var_names) - 1):
        ax = fig.add_subplot(len(var_names) - 1, 1, i + 1)
        ax.scatter(data[:, 0], data[:, i + 1], s=5, c='k')
        ax.set_xlabel('{}'.format(var_names[0]))
        ax.set_ylabel('{}'.format(var_names[i + 1]))
        if i == 0:
            plt.title('measurement file: ' + measure_file_model.title)

    # For the following block thanks to: https://stackoverflow.com/questions/
    # 20580179/saving-a-matplotlib-graph-as-an-image-field-in-database
    f = BytesIO()
    plt.savefig(f, bbox_inches='tight')
    plt.close(fig)
    content_file = ContentFile(f.getvalue())
    measure_file_model.scatter_plot.save('scatter_plot.png', content_file)
    measure_file_model.save()


def data_to_table(matrix, var_names):
    """
    The function adjusts the matrix generated by compute to fit in the table
    generation tool of the pdf framework.
    :param matrix:          data points. 
    :param var_names:       names of the variables. 
    :return:                adjusted table
    """
    table = []
    header = []
    header.append('#')
    for name in var_names:
        header.append(name)
    table.append(header)
    for i, x in enumerate(matrix[0][1]):
        row = []
        row.append(i)
        for j in range(len(matrix[0])):

            # The formating that is used is taken from https://stackoverflow.
            # com/questions/455612/limiting-floats-to-two-decimal-points
            row.append("{0:.2f}".format(matrix[0][j][i]))

        table.append(row)
    return table


def create_latex_report(contour_coordinates, user, environmental_contour,
                        var_names, var_symbols):
    """
    Creates a latex-based pdf report describing the performed environmental
    contour calculation.

    Makes use of the 'latex_report.tex' template where the document class and
    packages are defined.

    Parameters
    ----------
    contour_coordinates : n-dimensional matrix
        The coordinates of the environmental contour.
        The format is defined by compute_interface.iform()
    user : django.contrib.auth.models.User
        The user, who is working with the app. The report will be saved in a
        directory named like the user.
    environmental_contour : enviro.models.EnvironmentalContour
        Django's environmental contour model, which contains the contour's path,
        the options that were used to create it and its probabilistc model
    var_names : list of strings
        Names of the environmental variables used in the probabilistic model,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']
    var_symbols : list of strings
        Symbols of the environental variables used in the probabilistic model,
        e.g. ['V', 'Hs']

    Returns
    -------
    short_file_path_report : string,
        The path where the pdf, generated based latex, is saved
        The path continues after the static files prefix, which is defined in
        settings.py and currently is 'enviro/static/'

    """
    probabilistic_model = environmental_contour.probabilistic_model
    short_directory = settings.PATH_USER_GENERATED + user + \
                             '/contour/' + str(environmental_contour.pk) + '/'
    short_file_path_report = short_directory + settings.LATEX_REPORT_NAME
    full_directory = settings.PATH_MEDIA + short_directory
    full_file_path_report = settings.PATH_MEDIA + short_file_path_report


    plot_contour(contour_coordinates, user, environmental_contour, var_names)

    pf_contour = PlottedFigure.objects.filter(
        environmental_contour=environmental_contour).first()
    # Download the image from Amazon S3 since latex needs a local version
    url_contour_image = pf_contour.image.url
    local_path_contour_image = full_directory + \
                               os.path.split(url_contour_image)[1]
    if USE_S3:
        request.urlretrieve(url_contour_image, local_path_contour_image)

    directory_prefix = settings.PATH_MEDIA + settings.PATH_USER_GENERATED

    latex_content = r"\section{Results} " \
                    r"\subsection{Environmental contour}" \
                    r"\includegraphics[width=\textwidth]{" + \
                    local_path_contour_image+ r"}" \
                    r"\subsection{Extreme environmental design conditions}" + \
                    get_latex_eedc_table(
                        contour_coordinates,
                        var_names,
                        var_symbols) + \
                    r"\section{Methods}" \
                    r"\subsection{Associated measurement file}"

    if probabilistic_model.measure_file_model:
        latex_content += r"File: '\verb|" + \
                         probabilistic_model.measure_file_model.title + \
                         r"|' \subsection{Fitting}"
        plotted_figures = PlottedFigure.objects.filter(
            probabilistic_model=probabilistic_model)
        for plotted_figure in plotted_figures:
            url_plotted_figure = plotted_figure.image.url
            local_path_plotted_figure = full_directory + \
                                       os.path.split(url_plotted_figure)[1]
            request.urlretrieve(url_plotted_figure, local_path_plotted_figure)
            latex_content += r"\begin{figure}[H]"
            latex_content += r"\includegraphics[width=\textwidth]{" + \
                             local_path_plotted_figure + r"}"
            latex_content += r"\end{figure}"
    else:
        latex_content += r"No associated file. The model was created by " \
                         r"direct input."

    latex_content += r"\subsection{Probabilistic model}"
    latex_content += r"Name: '\verb|" + \
                     probabilistic_model.collection_name + \
                     r"|'\\"

    # Get the probability density function equation in latex style
    dists_model = DistributionModel.objects.filter(
        probabilistic_model=probabilistic_model)
    var_symbols = []
    for dist in dists_model:
        var_symbols.append(dist.symbol)
    multivariate_distribution = setup_mul_dist(probabilistic_model)
    latex_string_list = multivariate_distribution.latex_repr(var_symbols)

    latex_content += r"{\setlength{\mathindent}{0cm}"
    for latex_string in latex_string_list:
        latex_content += r"\begin{equation*}"
        latex_content += latex_string
        latex_content += r"\end{equation*}"
    latex_content += r"}"

    latex_content += r"\subsection{Environmental contour} \
        \begin{itemize}"
    latex_content += r"\item Contour method: "
    latex_content += environmental_contour.contour_method
    latex_content += r"\item Return period: "
    latex_content += str(environmental_contour.return_period) + " years"
    additonal_options = AdditionalContourOption.objects.filter(
        environmental_contour=environmental_contour)
    for additonal_option in additonal_options:
        key = additonal_option.option_key
        val = additonal_option.option_value
        latex_content += r"\item " + key + ": " + str(val)
    latex_content += r"\end{itemize}"

    render_dict = dict(
        content=latex_content
    )
    template = get_template('contour/latex_report.tex')
    rendered_tpl = template.render(render_dict).encode('utf-8')
    with tempfile.TemporaryDirectory() as tempdir:
        # Create subprocess, supress output with PIPE and
        # run latex twice to generate the TOC properly.
        # Finally read the generated pdf.
        for i in range(2):
            process = Popen(
                ['pdflatex', '--shell-escape', '-output-directory', tempdir],
                stdin=PIPE,
                stdout=PIPE,
            )
            process.communicate(rendered_tpl)
        with open(os.path.join(tempdir, 'texput.pdf'), 'rb') as f:
            pdf = f.read()

    if not os.path.exists(full_directory):
        os.makedirs(full_directory)
    with open(full_file_path_report, 'wb') as f:
        f.write(pdf)
        djangofile = ContentFile(pdf)
        environmental_contour.latex_report.save(
            settings.LATEX_REPORT_NAME, djangofile)
        environmental_contour.save()

    create_design_conditions_csv(contour_coordinates, environmental_contour)

    return short_file_path_report


def get_latex_eedc_table(matrix, var_names, var_symbols):
    """
    Creates a latex string containing a table listing the contour's extreme
    environmental design conditions (EEDCs).

    Parameters
    ----------
    matrix : n-dimensional matrix
        The coordinates of the environmental contour.
        The format is defined by compute_interface.iform()

    var_names : list of strings
        Names of the environmental variables used in the probabil. model,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']

    var_symbols : list of strings
        Symbols of the environental variables used in the probabil. model,
        e.g. ['V', 'Hs']

    Returns
    -------
    table_string : string,
        A string in latex format containing a table, which lists the first
        X extreme environmental design conditions

    """

    MAX_EEDCS_TO_LIST_IN_TABLE = 100
    LINES_FOR_PAGE_BREAK = 40

    reached_max_eedc_number = 0

    table_string = r"\begin{tabular}{"
    table_head_line = get_latex_eedc_table_head_line(var_names)
    table_string += table_head_line

    for i in range(len(matrix[0][1])):
        table_string += str(i + 1) + r" & "
        for j in range(len(var_names)):

            # The formating is taken from https://stackoverflow.com/questions/
            # 455612/limiting-floats-to-two-decimal-points
            table_string += "{0:.2f}".format(matrix[0][j][i])

            if j == len(var_names) - 1:
                table_string += r"\\"
            else:
                table_string += r" & "
        if i % LINES_FOR_PAGE_BREAK == 0 and i > 0:
            table_string += r"\end{tabular}"
            table_string += r"\newpage"
            table_string += r"\begin{tabular}{"
            table_string += table_head_line
        if i == MAX_EEDCS_TO_LIST_IN_TABLE - 1:
            reached_max_eedc_number = 1
            break

    table_string += r"\end{tabular} \vspace{1em} \newline "
    if reached_max_eedc_number:
        table_string += "Only the first " + str(MAX_EEDCS_TO_LIST_IN_TABLE) + \
                        " out of " + str(len(matrix[0][1])) + \
                        " EEDCs are listed."

    return table_string


def get_latex_eedc_table_head_line(var_names):
    """
    Creates a latex string containing the first line of a table.

    The table lists the contour's extreme environmental design
    conditions (EEDCs).

    Parameters
    ----------
    var_names : list of strings
        Names of the environmental variables used in the probabil. model,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']


    Returns
    -------
    head_line_string : string,
        A string in latex format containing the first row of the table,
        e.g. "EEDC & significant wave height [m] & peak period [s]\\"

    """

    head_line_string = ""

    for i in range(len(var_names) + 1):
        head_line_string += r" l"
    head_line_string += r" }"

    head_line_string += r"EEDC & "
    for i, x in enumerate(var_names):
        head_line_string += x
        if i == len(var_names) - 1:
            head_line_string += r"\\"
        else:
            head_line_string += r" & "

    return head_line_string


def create_design_conditions_csv(contour_coordinates, environmental_contour):
    """
    Creates a .csv file containing the extreme env. design conditions.

    The file is saved as a FileField of the EnvironmentalContour object.

    Parameters
    ----------
    contour_coordinates : n-dimensional matrix
        The coordinates of the environmental contour.
        The format is defined by compute_interface.iform().
    environmental_contour : EnvironmentalContour
        The django model of the environmental contour.

    """
    file_content_as_string = ""
    for i in range(len(contour_coordinates)):
        for j in range(len(contour_coordinates[0][0])):
            for k in range(len(contour_coordinates[0])):
                file_content_as_string += str(contour_coordinates[i][k][j])
                if k < (len(contour_coordinates[0]) - 1):
                    file_content_as_string += ";"
            file_content_as_string += "\n"
    content_bytes = file_content_as_string.encode('utf-8')
    content_file = ContentFile(content_bytes)
    environmental_contour.design_conditions_csv.save(
        settings.EEDC_FILE_NAME, content_file)
    environmental_contour.save()
