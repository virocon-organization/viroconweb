import pandas as pd
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.platypus import Paragraph, Spacer, Image, Table, TableStyle, Frame, BaseDocTemplate, PageTemplate
from reportlab.platypus.flowables import KeepTogether
import numpy as np
import os
import shutil
from .models import ProbabilisticModel, DistributionModel, ParameterModel
from scipy.stats import weibull_min
from scipy.stats import lognorm
from scipy.stats import norm
import warnings
import matplotlib
matplotlib.use('Agg') # thanks to https://stackoverflow.com/questions/41319082/import-matplotlib-failing-with-no-module-named-tkinter-on-heroku
import matplotlib.pyplot as plt
from .plot_generic import *
from descartes import PolygonPatch
from django.http import HttpResponse
from django.template import Context
from django.template.loader import get_template
from subprocess import Popen, PIPE
from .compute_interface import setup_mul_dist
import tempfile

IMAGE_FULL_WIDTH_REPORT = 16.26  # in cm
IMAGE_FULL_HEIGHT_REPORT = 12.19  # in cm

def plot_pdf_with_raw_data(main_index, parent_index, low_index, shape, loc, scale, distribution_type, dist_points, interval, var_name,
                           symbol_parent_var, directory):
    """
    The function creates an image which shows a certain fit of a distribution.
    :param main_index:      the index of the current variable (distribution). (needed to recognize the images later)
    :param parent_index     the index of the variable on which the conditional is based (when no condition: None)
    :param low_index:       the index of the interval. (needed to recognize the images later)
    :param shape:           the value of the shape parameter.
    :param loc:             the value of the loc parameter. (location)
    :param scale:           the value of the scale paramter.
    :param distribution_type:   Type / name of the distribution, must be "Normal", "Weibull" or "Lognormal"
    :param dist_points:     the dates for the histogram.
    :param interval:        interval of the plotted distribution.
    :param var_name:        the name of a single variable of the probabilistic model. 
    :param symbol_parent_var:      symbol of the variable on which the conditional variable is based.
    :param directory        the directory where the figure should be saved
    :return: 
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)

    if distribution_type == 'Normal':
        x = np.linspace(norm.ppf(0.0001, loc, scale), norm.ppf(0.9999, loc, scale), 100)
        y = norm.pdf(x, loc, scale)
        text = distribution_type + ', ' + 'mu: ' + str(format(loc, '.3f')) + ' sigma: ' + str(format(scale, '.3f'))
    elif distribution_type == 'Weibull':
        x = np.linspace(weibull_min.ppf(0.0001, shape, loc, scale), weibull_min.ppf(0.9999, shape, loc, scale), 100)
        y = weibull_min.pdf(x, shape, loc, scale)
        text = distribution_type + ', ' + 'shape: ' + str(format(shape, '.3f')) + ' loc: ' + str(
            format(loc, '.3f')) + ' scale: ' + str(format(scale, '.3f'))
    elif distribution_type == 'Lognormal':
        scale = np.exp(scale) # scale parameter for python lognorm = e^\mu, however in the django data base we save mu as the sacle parameter
        x = np.linspace(lognorm.ppf(0.0001, shape, scale=scale), lognorm.ppf(0.9999, shape, scale=scale), 100)
        y = lognorm.pdf(x, shape, scale=scale)
        text = distribution_type + ', ' + 'sigma: ' + str(format(shape, '.3f')) + ' mu: ' + str(format(np.log(scale), '.3f'))
    else:
        raise KeyError('No function match - {}'.format(distribution_type))

    text = text + ' ('
    if symbol_parent_var:
        text = text + str(format(interval[0], '.3f')) + '≤' + symbol_parent_var + '<' + str(
            format(interval[1], '.3f')) + ', '
    text = text + 'n=' + str(len(dist_points)) + ')'

    ax.plot(x, y, 'r-', lw=5, alpha=0.6, label=distribution_type)
    n_intervals_histogram = int(round(len(dist_points)/50.0))
    if n_intervals_histogram > 100:
        n_intervals_histogram = 100
    if n_intervals_histogram < 10:
        n_intervals_histogram = 10

    ax.hist(dist_points, n_intervals_histogram, normed=True, histtype='stepfilled', alpha=0.9, color='#54889c')

    ax.grid(True)

    plt.title(text)
    plt.xlabel(var_name)
    plt.ylabel('probability density [-]')
    main_index_2_digits = str(main_index).zfill(2)
    parent_index_2_digits = str(parent_index).zfill(2)
    low_index_2_digits = str(low_index).zfill(2)
    # convention for name: fit_01_00_02.png (would mean a plot of the second variable (01) which is conditional on the
    # first variable (00) and this is the third (02) fit
    plt.savefig(directory + '/fit_' + main_index_2_digits + '_' + parent_index_2_digits + '_' + low_index_2_digits + '.png')
    plt.close(fig)
    return


def plot_parameter_fit_overview(main_index, var_name, var_symbol, para_name, data_points, fit_func, directory, dist_name):
    """
    The function plots an image which shows the fit of a function. 
    :param main_index:      index of the related distribution.
    :param var_name:        name of the variable (distribution).
    :param var_symbol:      symbol of the variables of the probabilistic model
    :param para_name:       parameter name like shape, location, scale.
    :param data_points:     data point for every interval.
    :param fit_func:        the fit function - polynomial, exponential ..
    :param directory:       directory where the figure should be saved.
    :param dist_name        name of the distribution, e.g. "Lognormal"
    """
    if dist_name == 'Weibull':
        if para_name == 'shape':
            y_text = 'k (shape)'
        elif para_name == 'location':
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
        elif para_name == 'location':
            y_text = 'μ (mean)'
        elif para_name == 'scale':
            y_text = 'σ (standard deviation)'
    else:
        y_text = para_name

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # generate data points from the fitted function
    x = np.linspace(min(data_points[0]) - 2, max(data_points[0]) + 2, 100)
    y = []
    for x1 in x:
        y.append(fit_func._value(x1))

    #if dist_name == 'Lognormal' and para_name == 'scale':
        #y = np.log(y)

    # plot generate data points
    ax.plot(x, y, color='#54889c')

    # plot interval based data points
    ax.scatter(data_points[0], data_points[1], color='#9C373A')

    ax.grid(True)
    plt.title('Variable: ' + var_name)
    plt.ylabel(y_text)
    plt.xlabel(var_name)
    plt.savefig(directory + '/fit_' + str(main_index) + para_name + '.png')
    plt.close(fig)


def plot_fits(fit, var_names, var_symbols, title, user, measure_file, directory):
    """
    The function distributes the information given by the parameters and starts the plot assignment. 
    The Distribution of the parameters depends on the dependencies between the variables of a probabilistic model. 
    There are 9 possibilities. The structure of the possibilities is like a truth table. 
    :param fit:             fit results
                            distribution. (Further information in the doc from compute)
    :param var_names:       the names of the single variables of the probabilistic model.
    :param var_symbols:     symbols of the variables of the probabilistic model
    :param title:           the title of the probabilistic model.
    :param user:            the user who started the request (to assign the images later).
    :param directory:       directory where the figures should be saved (the primary key will be added as a subfolder)
    :return:                the primary key of the created probabilistic model instance.
    """
    probabilistic_model = ProbabilisticModel(primary_user=user, collection_name=title, measure_file_model=measure_file)
    probabilistic_model.save()

    # deletes the results form further fits for a specific user.
    #path = 'enviro/static/' + str(user)
    #if os.path.isdir(path):
    #    shutil.rmtree(path)
    #if not os.path.exists(path):
    #    os.makedirs(path)
    directory = directory + '/' + str(probabilistic_model.pk)
    if not os.path.exists(directory):
        os.makedirs(directory)

    params = ['shape', 'location', 'scale']
    mult_float_points = []
    interval_centers = []

    # prepare data to plot a function and save the data into the database tables
    for i, param_points in enumerate(fit.mul_param_points):
        distribution = fit.mul_var_dist.distributions[i]
        list_float_points = []
        name = 'Lognormal_2' if (distribution.name == 'Lognormal') else distribution.name
        distribution_model = DistributionModel(name=var_names[i], distribution=name,
                                               symbol=var_symbols[i], probabilistic_model=probabilistic_model)
        distribution_model.save()

        for j, spec_param_points in enumerate(param_points):
            float_points = []
            # selects which parameter is currently  processed
            if j == 0:
                param = distribution.shape
            elif j == 1:
                param = distribution.loc
            elif j == 2:
                if name == 'Lognormal_2':
                    param = distribution.mu
                else:
                    param = distribution.scale
            else:
                raise KeyError('{} is not a matching index of a parameter like shape location and scale'.format(
                    distribution.param))
            if spec_param_points is not None:
                for k, point in enumerate(spec_param_points[1]):
                    float_points.append(point)
                    interval_centers.append(spec_param_points[0][k])
                plot_parameter_fit_overview(i, var_names[i], var_symbols[i], params[j], [spec_param_points[0], float_points],
                                            param, directory, distribution.name)
                parameter_model = ParameterModel(function=param.func_name, x0=param.a, x1=param.b, x2=param.c,
                                                 dependency=fit.mul_var_dist.dependencies[i][j],
                                                 distribution=distribution_model)

            else:
                if param is None:
                    for k in range(fit.dist_descriptions[i].get('used_number_of_intervals')):
                        float_points.append(0)
                    parameter_model = ParameterModel(function='None', x0=0, dependency='!',
                                                     distribution=distribution_model)
                else:
                    for k in range(fit.dist_descriptions[i].get('used_number_of_intervals')):
                        float_points.append(param._value(1))
                    parameter_model = ParameterModel(function='None', x0=param._value(1), dependency='!',
                                                     distribution=distribution_model)

            MAX_VALID_VALUE_COEFF = 1000000
            if parameter_model.x0 > MAX_VALID_VALUE_COEFF or parameter_model.x0 < -1*MAX_VALID_VALUE_COEFF:
                raise ValueError('The value of the fitting coefficient is invalid. Maybe this was caused by having too'
                                 ' little data for the fit. Or the wrong distribution was selected.') # These values could cause probblems in the data base see issue 19
            parameter_model.save()

            list_float_points.append(float_points)
        mult_float_points.append(list_float_points)

    # prepare data to plot a distribution
    for i, dist_points in enumerate(fit.mul_dist_points): # i = the variable index
        #print ('dist_points type: ' + str(type(dist_points)) + ', of length: ' + str(len(dist_points)))
        for j, spec_dist_points in enumerate(dist_points): # j = 0-2 (shape, loc, scale)
            for k, dist_point in enumerate(spec_dist_points): # k = number of intervals
                if i == 0 or len(interval_centers) < 2:
                    interval_limits = [min(interval_centers), max(interval_centers)]
                else:
                    interval_width = interval_centers[1] - interval_centers[0] # assuming constant interval width
                    interval_limits = [interval_centers[k] - 0.5 * interval_width, interval_centers[k] + 0.5*interval_width]
                parent_index = fit.mul_var_dist.dependencies[i][j]
                symbol_parent_var = None
                if parent_index is not None:
                    symbol_parent_var = var_symbols[parent_index]
                if is_legit_distribution_parameter_index(fit.mul_var_dist.distributions[i].name, j):
                    plot_pdf_with_raw_data(i, parent_index, k, mult_float_points[i][0][k], mult_float_points[i][1][k],
                                               mult_float_points[i][2][k], fit.mul_var_dist.distributions[i].name, dist_point, interval_limits,
                                               var_names[i], symbol_parent_var, directory)
                if i == 0: # first variable has no dependencies --> no need to check
                    break
    return probabilistic_model

def is_legit_distribution_parameter_index(distribution_name, index):
    """
    Check if the distribution has this kind of parameter index (0 = shape, 1 = loc, 2 = scale)
    """
    if distribution_name=='Normal':
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
        warnings.warn("The distribution name you used to call is_legit_distribution_parameter_index() is not supported")
        return False


def get_first_number_of_tuple(x):
    """
    Finds the first integer number of a tuple and returns it.
    :param x:           the tuple
    """
    first_number = None
    for i in range(len(x)):
        if type(x[i])==int:
            first_number = x[i]
            break

    return first_number


def plot_contour(matrix, user, method_label, probabilistic_model, var_names, var_symbols, method):
    """
    The function plots a png image of a contour.
    :param matrix:      data points of the contour
    :param user:        who gives the contour calculation order
    :param method_label:      e.g. "T = 25 years, IFORM"
    :param probabilistic_model:       probabilistic model object
    :param var_names:   name of the variables of the probabilistic model
    :param var_symbols: symbols of the variables of the probabilistic model
    """

    path = 'enviro/static/' + str(user)
    #if os.path.isdir(path):
        #shutil.rmtree(path)
    if not os.path.exists(path):
        os.makedirs(path)

    fig = plt.figure()

    if len(matrix[0]) == 2:
        ax = fig.add_subplot(111)

        # plot raw data
        if (probabilistic_model.measure_file_model):
            data_path = probabilistic_model.measure_file_model.measure_file.url
            data_path = data_path[1:]
            data = pd.read_csv(data_path, sep=';', header=0).as_matrix()
            ax.scatter(data[:,0], data[:,1], s=5 ,c='k', label='measured/simulated data')

        # plot contour
        alpha = .1
        for i in range(len(matrix)):
            ax.scatter(matrix[i][0], matrix[i][1], s=15, c='b',label='extreme env. design condition')
            #ax.plot(matrix[i][0], matrix[i][1], 'b-')
            concave_hull, edge_points = alpha_shape(convert_ndarray_list_to_multipoint(matrix[i]), alpha=alpha)

            patch_design_region = PolygonPatch(concave_hull, fc='#999999', linestyle='None', fill=True,
                                 zorder=-2, label='design region')
            patch_environmental_contour = PolygonPatch(concave_hull, ec='b', fill=False,
                                 zorder=-1, label='environmental contour')
            ax.add_patch(patch_design_region)
            ax.add_patch(patch_environmental_contour)


        plt.legend(loc='lower right')
        plt.xlabel('{}'.format(var_names[0]))
        plt.ylabel('{}'.format(var_names[1]))
    elif len(matrix[0]) == 3:
        ax = fig.add_subplot(1, 1, 1, projection='3d')

        #ax.plot_trisurf(matrix[0][0], matrix[0][1], matrix[0][2], linewidth=0.2, antialiased=False)
        ax.scatter(matrix[0][0], matrix[0][1], matrix[0][2], marker='o', c='r')

        ax.set_xlabel('{}'.format(var_names[0]))
        ax.set_ylabel('{}'.format(var_names[1]))
        ax.set_zlabel('{}'.format(var_names[2]))
    else:
        ax = fig.add_subplot(111)
        plt.figtext(0.5, 0.5, '4-Dim plot is not supported')
        warnings.warn("4-Dim plot or higher is not supported", DeprecationWarning, stacklevel=2)

    ax.grid(True)
    plt.title(probabilistic_model.collection_name + ': ' + method_label)

    short_path = user + '/contour.png'
    plt.savefig('enviro/static/' + short_path, bbox_inches='tight')
    plt.close(fig)

def plot_data_set_as_scatter(user, measure_file_model, var_names, directory):
    fig = plt.figure(figsize=(7.5, 5.5*(len(var_names)-1)))
    data_path = measure_file_model.measure_file.url
    data_path = data_path[1:]
    data = pd.read_csv(data_path, sep=';', header=0).as_matrix() #0 is right! 1 caused a bug where the first data row is ignored, see issue #20
    for i in range(len(var_names)-1):
        ax = fig.add_subplot(len(var_names)-1,1,i+1)
        ax.scatter(data[:, 0], data[:, i+1], s=5, c='k')
        ax.set_xlabel('{}'.format(var_names[0]))
        ax.set_ylabel('{}'.format(var_names[i+1]))
        if i==0:
            plt.title('measurement file: ' + measure_file_model.title)
    if not os.path.exists(directory):
        os.makedirs(directory)
    plt.savefig(directory + '/scatter.png', bbox_inches='tight')
    plt.close(fig)

def data_to_table(matrix, var_names):
    """
    The function adjusts the matrix generated by compute to fit in the table generation tool of the pdf framework.
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
            row.append("{0:.2f}".format(matrix[0][j][i])) # thanks to https://stackoverflow.com/questions/455612/limiting-floats-to-two-decimal-points
        table.append(row)
    return table


# TODO @Felix docstrings!
def define_header_and_footer(canvas, doc):
    """

    :param canvas: 
    :param doc: 
    :return: 
    """
    canvas.saveState()
    #header_content = Image('static/images/ViroVektorCWithDevelopedBy.jpg', width=8 * cm, height=3.819 * cm)
    header_content = Image('static/images/ViroVektorC.jpg', width=5 * cm, height=1.375 * cm)
    #footer_content = Image('static/images/Footy2.jpg', width=21 * cm, height=3 * cm)
    #w, h = footer_content.wrap(doc.width, doc.bottomMargin)
    #footer_content.drawOn(canvas, 0, 0)
    w, h = header_content.wrap(doc.width, doc.topMargin)
    header_content.drawOn(canvas, 8 * cm, doc.height + doc.topMargin - h)
    canvas.restoreState()


def plot_pdf(matrix, user, method_label, probabilistic_model, var_names, var_symbols, method):
    """
    The function generates a pdf. The pdf includes an image of the contour and a table with the data points.
    :param matrix:      data points supported by compute. 
    :param user:        who starts the order. 
    :param method_label:      e.g. "T = 25 years, IFORM"
    :param probabilistic_model:       probabilistic model object.
    :param var_names:   names of the variables.
    :param var_symbols: symbols of the variables of the probabilistic model
    :return:            the path to the user related pdf.
    """

    plot_contour(matrix, user, method_label, probabilistic_model, var_names, var_symbols, method)

    story = []
    styles = getSampleStyleSheet()
    styleN = styles['Normal']

    # add title for graph
    story.append(Paragraph("<strong>1. Results</strong>", styleN))
    story.append(Paragraph("<strong>1.1 Environmental contour</strong>", styleN))
    story.append(Spacer(1, .25 * inch))

    # add graph
    file_path_contour = 'enviro/static/' + user + '/contour.png'
    story.append(Image(file_path_contour, width=IMAGE_FULL_WIDTH_REPORT * cm, height=IMAGE_FULL_HEIGHT_REPORT * cm))
    story.append(Spacer(1, .5 * inch))

    # add title for extreme environmental conditions
    story.append(Paragraph("<strong>1.2 Extreme environmental design conditions</strong>", styleN))
    story.append(Spacer(1, .25 * inch))

    # add table
    if len(matrix[0][0])<=200:
        table_data = data_to_table(matrix, var_names)
        t = Table(table_data, 100, 25)
        grid_style = TableStyle([('GRID', (0, 0), (-1, -1), 0.25, colors.black), ('ALIGN', (1, 1), (-1, -1), 'RIGHT')])
        t.setStyle(grid_style)
        story.append(KeepTogether(t))
        story.append(Spacer(1, .5 * inch))
    else:
        story.append(Paragraph("The table is not plotted since a maximum of 200 extreme environmental design conditions"
                               " are supported. Based on your input we computed " + str(len(matrix[0][0])) + " conditions.", styleN))
        story.append(Spacer(1, .25 * inch))

    story.append(Paragraph("<strong>2. Methods </strong>", styleN))
    story.append(Paragraph("<strong>2.1. Associated measurement file</strong>", styleN))
    if probabilistic_model.measure_file_model:
        story.append(Paragraph("File: '" + probabilistic_model.measure_file_model.title +"'", styleN))
        file_path_scatter = 'enviro/static/' + user + '/scatter.png'
        story.append(Image(file_path_scatter, width=IMAGE_FULL_WIDTH_REPORT * cm, height=IMAGE_FULL_HEIGHT_REPORT * cm))
        story.append(Spacer(1, .25 * inch))
    else:
        story.append(Paragraph("There is no associated measurement file.", styleN))
    story.append(Paragraph("<strong>2.2. Fitting</strong>", styleN))
    if probabilistic_model.measure_file_model:
        story.append(Paragraph("<strong>2.2.1 Probability density function</strong>", styleN))
        story.append(Paragraph("<strong>2.2.2 Goodness of fit</strong>", styleN))
        directory_prefix = 'enviro/static/'
        directory_after_static = user + '/prob_model/' + str(probabilistic_model.pk)
        directory = directory_prefix + directory_after_static
        if os.path.isdir(directory):
            img_list = os.listdir(directory)
            for img in img_list:
                story.append(Image(directory + '/' + img, width=0.65*IMAGE_FULL_WIDTH_REPORT * cm, height=0.65*IMAGE_FULL_HEIGHT_REPORT * cm))
                story.append(Spacer(1, .25 * inch))
    else:
        story.append(Paragraph("There is no fit.", styleN))

    story.append(Paragraph("<strong>2.3. Probabilistic model</strong>", styleN))
    story.append(Paragraph("<strong>2.4. Environmental contour</strong>", styleN))

    # build Story into Document Template
    short_file_path_report = user + '/contour_table.pdf'
    doc = BaseDocTemplate(filename='enviro/static/' + short_file_path_report)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 2 * cm, )
    template = PageTemplate(id='test', frames=frame, onPage=define_header_and_footer)
    doc.addPageTemplates([template])
    doc.build(story)

    return short_file_path_report

def create_latex_report(matrix, user, method_label, probabilistic_model, var_names, var_symbols, method):
    plot_contour(matrix, user, method_label, probabilistic_model, var_names, var_symbols, method)
    directory_prefix = 'enviro/static/'
    file_path_contour = directory_prefix + user + '/contour.png'
    directory_fit_images = directory_prefix + user + '/prob_model/'
    img_list = os.listdir(directory_fit_images + '/' + str(probabilistic_model.pk))


    print("measure file: " + probabilistic_model.measure_file_model.title)

    latex_content = r"""\section{Results}
                \subsection{Environmental contour}
                \includegraphics[width=\textwidth]{""" + file_path_contour + r"""}
                \subsection{Extreme environmental design conditions}"""\
                    + get_latex_eedc_table(var_names, var_symbols, matrix) + r"""
                \section{Methods}
                \subsection{Associated measurement file}"""
    if probabilistic_model.measure_file_model:
        latex_content += r"""file: '\verb|""" + probabilistic_model.measure_file_model.title + r"""|'
                \subsection{Fitting}"""
        for img in img_list:
            img_name = directory_fit_images + str(probabilistic_model.pk) + "/" + img
            latex_content += r"""\begin{figure}[H]"""
            latex_content += r"""\includegraphics[width=\textwidth]{""" + img_name + r"""}"""
            latex_content += r"""\end{figure}"""
    else:
        latex_content += r"""No associated file. The model was created by direct input."""

    latex_content += r"""\subsection{Probabilistic model}"""

    # get the equation in latex style
    dists_model = DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
    var_symbols = []
    for dist in dists_model:
        var_symbols.append(dist.symbol)
    multivariate_distribution = setup_mul_dist(probabilistic_model)
    latex_string_list = multivariate_distribution.getPdfAsLatexString(var_symbols)

    for latex_string in latex_string_list:
        latex_content += r"""\begin{equation*}"""
        latex_content += latex_string
        latex_content += r"""\end{equation*}"""
    latex_content += r"""\subsection{Environmental contour}
        \begin{itemize}"""
    #    \item Fitting method: """
    #latex_content += method.fitting_method
    latex_content += r"""\item Contour method: """
    latex_content += method.contour_method
    latex_content += r"""\item Return period: """
    latex_content += str(method.return_period) + " years"
    for key, val in method.additional_options.items():
        latex_content += r"""\item """ + key + ": " + str(val)
    latex_content += r"""\end{itemize}"""

    print("file_path_contour: " + file_path_contour)

    print("latex_content:")
    print(latex_content)
    render_dict = dict(
        content=latex_content
        )
    template = get_template('enviro/latex_report.tex')
    rendered_tpl = template.render(render_dict).encode('utf-8')
    # Python3 only. For python2 check out the docs!
    with tempfile.TemporaryDirectory() as tempdir:
        # Create subprocess, supress output with PIPE and
        # run latex twice to generate the TOC properly.
        # Finally read the generated pdf.
        for i in range(2):
            process = Popen(
                ['pdflatex', '-output-directory', tempdir],
                stdin=PIPE,
                stdout=PIPE,
            )
            process.communicate(rendered_tpl)
        with open(os.path.join(tempdir, 'texput.pdf'), 'rb') as f:
            pdf = f.read()


        short_file_path_report = user + '/latex_report.pdf'
        full_file_path_report = 'enviro/static/' + short_file_path_report
        with open(full_file_path_report, 'wb') as f:
            f.write(pdf)

    return short_file_path_report

def get_latex_eedc_table(var_names, var_symbols, matrix):
    table_string = r"\begin{tabular}{"
    for i in range(len(var_names) + 1):
        table_string += r" l"
    table_string += r" }"

    table_string += r"EEDC & "
    for i, x in enumerate(var_names):
        table_string += x
        if i == len(var_names) - 1:
            table_string += r"\\"
        else:
            table_string += r" & "

    for i in range(len(matrix[0][1])):
        table_string += r"" + str(i+1) + r" & "
        for j in range(len(var_names)):
            table_string += "{0:.2f}".format(matrix[0][j][i]) # thanks to https://stackoverflow.com/questions/455612/limiting-floats-to-two-decimal-points
            if j == len(var_names) - 1:
                table_string += r"\\"
            else:
                table_string += r" & "
    table_string += r"\end{tabular}"

    return table_string
