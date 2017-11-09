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
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.tri as mtri

def plot_pdf_with_raw_data(main_index, low_index, shape, loc, scale, form, dist_points, interval, var_name, symbol_parent_var, user):
    """
    The function creates an image which shows a certain fit of a distribution.
    :param main_index:      the index of the current variable (distribution). (needed to recognize the images later)
    :param low_index:       the index of the step parameter. (needed to recognize the images later)
    :param shape:           the value of the shape parameter.
    :param loc:             the value of the loc parameter. (location)
    :param scale:           the value of the scale paramter.
    :param form:            the form of the distribution. (example: weibull)
    :param dist_points:     the dates for the histogram.
    :param interval:        interval of the plotted distribution.
    :param var_name:        the name of a single variable of the probabilistic model. 
    :param symbol_parent_var:      symbol of the variable on which the conditional variable is based.
    :param user:            the user who started the request (to assign the images later).
    :return: 
    """
    fig = plt.figure()
    ax = fig.add_subplot(111)

    if form == 'Normal':
        x = np.linspace(norm.ppf(0.0001, loc, scale), norm.ppf(0.9999, loc, scale), 100)
        y = norm.pdf(x, loc, scale)
        text = form + ', ' + 'mu: ' + str(format(loc, '.3f')) + ' sigma: ' + str(format(scale, '.3f'))
    elif form == 'Weibull':
        x = np.linspace(weibull_min.ppf(0.0001, shape, loc, scale), weibull_min.ppf(0.9999, shape, loc, scale), 100)
        y = weibull_min.pdf(x, shape, loc, scale)
        text = form + ', ' + 'shape: ' + str(format(shape, '.3f')) + ' loc: ' + str(
            format(loc, '.3f')) + ' scale: ' + str(format(scale, '.3f'))
    elif form == 'Lognormal':
        scale = np.exp(scale)
        x = np.linspace(lognorm.ppf(0.0001, shape, scale=scale), lognorm.ppf(0.9999, shape, scale=scale), 100)
        y = lognorm.pdf(x, shape, scale=scale)
        text = form + ', ' + 'sigma: ' + str(format(shape, '.3f')) + ' mu: ' + str(format(scale, '.3f'))
    else:
        raise KeyError('No function match - {}'.format(form))
    print('symbol_parent_var: ')
    print(symbol_parent_var)
    if symbol_parent_var:
        text = text + ', ' + str(format(interval[0], '.3f')) + '<' + symbol_parent_var + '<' + str(
            format(interval[1], '.3f'))

    ax.plot(x, y, 'r-', lw=5, alpha=0.6, label=form)

    ax.hist(dist_points, 100, normed=True, histtype='stepfilled', alpha=0.9, color='#54889c')

    ax.grid(True)

    plt.title(text)
    plt.xlabel(var_name)
    plt.ylabel('probability density [-]')
    plt.savefig('enviro/static/' + str(user) + '/fit_' + str(main_index) + str(low_index) + '.png')
    plt.close(fig)
    return


def plot_parameter_fit_overview(main_index, var_name, var_symbol, para_name, data_points, fit_func, user, dist_name):
    """
    The function plots an image which shows the fit of a function. 
    :param main_index:      index of the related distribution.
    :param var_name:        name of the variable (distribution).
    :param var_symbol:      symbol of the variables of the probabilistic model
    :param para_name:       parameter name like shape, location, scale.
    :param data_points:     data point for every interval.
    :param fit_func:        the fit function - polynomial, exponential ..
    :param user:            the user who starte the fit order.
    """
    print(dist_name)
    print(para_name)
    if dist_name == 'Lognormal':
        if para_name == 'scale':
            y_text = 'mu'
        elif para_name == 'shape':
            y_text = 'sigma'
    elif dist_name == 'Normal':
        if para_name == 'shape':
            return
        elif para_name == 'location':
            y_text = 'mu (mean)'
        elif para_name == 'scale':
            y_text = 'sigma (variance)'
    else:
        y_text = para_name

    fig = plt.figure()
    ax = fig.add_subplot(111)

    # generate data points from the fitted function
    x = np.linspace(min(data_points[0]) - 2, max(data_points[0]) + 2, 100)
    y = []
    for x1 in x:
        y.append(fit_func._value(x1))

    # plot generate data points
    ax.plot(x, y, color='#54889c')

    # plot interval based data points
    ax.scatter(data_points[0], data_points[1], color='#9C373A')

    ax.grid(True)
    plt.title('Variable: ' + var_name)
    plt.ylabel(y_text)
    plt.xlabel(var_name)
    plt.savefig('enviro/static/' + str(user) + '/fit_' + str(main_index) + para_name + '.png')
    plt.close(fig)


def plot_fits(fit, var_names, var_symbols, title, user, measure_file):
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
    :return:                the primary key of the created MeasureFileManager instance.
    """
    probabilistic_model = ProbabilisticModel(primary_user=user, collection_name=title, measure_file_model=measure_file)
    probabilistic_model.save()

    # deletes the results form further fits for a specific user.
    path = 'enviro/static/' + str(user)
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)

    params = ['shape', 'location', 'scale']
    mult_float_points = []
    intervals = []
    intervals.append(0.00)

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
                param = distribution.scale
            else:
                raise KeyError('{} is not a matching index of a parameter like shape location and scale'.format(
                    distribution.param))
            if spec_param_points is not None:
                for k, point in enumerate(spec_param_points[1]):
                    float_points.append(point)
                    intervals.append(spec_param_points[0][k])
                plot_parameter_fit_overview(i, var_names[i], var_symbols[i], params[j], [spec_param_points[0], float_points],
                                            param, user, distribution.name)
                parameter_model = ParameterModel(function=param.func_name, x0=param.a, x1=param.b, x2=param.c,
                                                 dependency=fit.mul_var_dist.dependencies[i][j],
                                                 distribution=distribution_model)

            else:

                if param is None:
                    for k in range(fit.n_steps):
                        float_points.append(0)
                    parameter_model = ParameterModel(function='None', x0=0, dependency='!',
                                                     distribution=distribution_model)
                else:
                    for k in range(fit.n_steps):
                        float_points.append(param._value(1))
                    parameter_model = ParameterModel(function='None', x0=param._value(1), dependency='!',
                                                     distribution=distribution_model)

            parameter_model.save()

            list_float_points.append(float_points)
        mult_float_points.append(list_float_points)

    # prepare data to plot a distribution
    for i, dist_points in enumerate(fit.mul_dist_points):
        for j, spec_dist_points in enumerate(dist_points):
            finisher = 0
            for k, dist_point in enumerate(spec_dist_points):
                if i == 0 or len(intervals) < 2:
                    interval = [min(intervals), max(intervals)]
                else:
                    interval = [intervals[k], intervals[k + 1]]


                symbol_parent_var = None
                if type(get_first_number_of_tuple(fit.mul_var_dist.dependencies[i]))==int:
                    symbol_parent_var = var_symbols[get_first_number_of_tuple(fit.mul_var_dist.dependencies[i])]

                print(fit.mul_var_dist.dependencies)
                print(var_symbols)
                print(symbol_parent_var)

                plot_pdf_with_raw_data(i, k, mult_float_points[i][0][k], mult_float_points[i][1][k], mult_float_points[i][2][k],
                                       fit.mul_var_dist.distributions[i].name, dist_point, interval,
                                       var_names[i], symbol_parent_var, user)
                finisher = k
            # acceleration
            if finisher == fit.n_steps - 1 or i == 0:
                break
    return probabilistic_model.pk

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
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path)

    fig = plt.figure()

    if len(matrix[0]) == 2:
        ax = fig.add_subplot(111)

        # plot raw data
        if (probabilistic_model.measure_file_model):
            data_path = probabilistic_model.measure_file_model.measure_file.url
            data_path = data_path[1:]
            data = pd.read_csv(data_path, sep=';', header=1).as_matrix()
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

def plot_data_set_as_scatter(user, measure_file_model, var_names):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    data_path = measure_file_model.measure_file.url
    data_path = data_path[1:]
    data = pd.read_csv(data_path, sep=';', header=1).as_matrix()
    ax.scatter(data[:, 0], data[:, 1], s=5, c='k')
    ax.set_xlabel('{}'.format(var_names[0]))
    ax.set_ylabel('{}'.format(var_names[1]))


    short_path = str(user) + '/scatter.png'
    plt.savefig('enviro/static/' + short_path, bbox_inches='tight')
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
    story.append(Paragraph("<strong>Results: Environmental contour</strong>", styleN))
    story.append(Spacer(1, .25 * inch))

    # add graph
    short_path = user + '/contour.png'
    story.append(Image('enviro/static/' + short_path, width=16.26 * cm, height=12.19 * cm))
    story.append(Spacer(1, .5 * inch))

    # add title for extreme environmental conditions
    story.append(Paragraph("<strong>Results: Extreme environmental design conditions</strong>", styleN))
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
                               " are supported. Based on your input we computed " + str(len(matrix[0][0])) + " conditions", styleN))
        story.append(Spacer(1, .25 * inch))

    # build Story into Document Template
    short_path = user + '/contour_table.pdf'
    doc = BaseDocTemplate(filename='enviro/static/' + short_path)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 2 * cm, )
    template = PageTemplate(id='test', frames=frame, onPage=define_header_and_footer)
    doc.addPageTemplates([template])
    doc.build(story)
    return short_path
