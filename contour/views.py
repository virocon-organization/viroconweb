import os
import csv
import warnings
import codecs
import time
# These imports and the setup() call is recuired for multiprocessing, see
# https://stackoverflow.com/questions/46908035/apps-arent-loaded-yet-
# exception-occurs-when-using-multi-processing-in-django
import django
django.setup()

from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404, HttpResponse, \
    HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse
from multiprocessing import Pool, TimeoutError
from urllib import request
from abc import abstractmethod

from . import forms
from . import models
from . import plot
from . import settings

from .models import User, MeasureFileModel, EnvironmentalContour, ContourPath, \
    ExtremeEnvDesignCondition, EEDCScalar, AdditionalContourOption, \
    ProbabilisticModel, DistributionModel, ParameterModel, PlottedFigure

from .compute_interface import ComputeInterface
from .validators import validate_contour_coordinates
from viroconcom import distributions, params
from .settings import MAX_COMPUTING_TIME, DO_SAVE_CONTOUR_COORDINATES_IN_DB


CONTOUR_CALCULATION_ERROR_MSG = 'Please consider different settings for the ' \
                                'contour or think about your probabilistic ' \
                                'model. Feel free to contact us if you ' \
                                'think this error is caused by a bug: ' \
                                'virocon@uni-bremen.de'
CONTOUR_REPORT_ERROR_MSG = 'An error occured when trying to generate ' \
                           'the report for the contour. ' \
                           'Feel free to contact us if you ' \
                           'think this error is caused by a bug: ' \
                           'virocon@uni-bremen.de'
DATA_BASE_TIME_OUT_ERROR_MSG = "Writing to the data base takes too long. " \
                               "It takes longer than the given value for a " \
                               "timeout, which is " \
                               "'{} seconds'.".format(
                                MAX_COMPUTING_TIME)
FITTING_ERROR_MSG = 'An error occured while fitting a probabliistic model ' \
                    'to the file. Feel free to contact us if you ' \
                    'think this error is caused by a bug: ' \
                    'virocon@uni-bremen.de'



def index(request):
    return render(request, 'contour/home.html')


class Handler:
    @staticmethod
    def overview(request, collection):
        """
        The method overview shows a overview of all items in a specific database.
        :param request:     to load an overview of database model.
        :param collection:  the selected database.       
        :return:            HttpResponse. 
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            meas = collection.objects.all()  # better name
            context = set()
            for item in meas:
                bool_ = False
                for secUser in item.secondary_user.all():
                    if secUser == request.user:
                        bool_ = True
                if bool_:
                    context.add(item)
                elif item.primary_user == request.user:
                    context.add(item)

            base = 'contour:' + collection.url_str()
            html = 'contour/' + collection.url_str() + '_overview.html'
            update = base + '_update'
            delete = base + '_delete'
            add = base + '_add'
            calc = base + '_calc'

            return render(request, html, {'context': context,
                                          'name': collection,
                                          'update': update,
                                          'delete': delete,
                                          'add': add,
                                          'calc': calc})

    @staticmethod
    def delete(request, pk, collection):
        """
        The method deletes a specific item from the database
        :param request:     to delete an item.
        :param collection:  the selected database
        :param pk:          the primary key from a specific item from the database          
        :return:            HttpResponse.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            instance = get_object_or_404(collection, pk=pk)
            if hasattr(instance, 'primary_user'):
                if instance.primary_user == request.user:
                    instance.delete()
                else:
                    instance.secondary_user.remove(request.user)
            else:
                instance.delete()
            redirection = 'contour:' + collection.url_str() + '_overview'
            return redirect(redirection)

    @staticmethod
    def update(request, pk, collection):
        """
        The method updates a specific item from the database
        :param request:     to update an item.
        :param collection:  the selected database.
        :param pk:          the primary key from a specific item from the database.
        :return:            HttpResponse.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            redirection = 'contour:' + collection.url_str() + '_overview'
            template = 'contour/update_sec_user.html'
            if request.method == 'POST':
                instance = get_object_or_404(collection, pk=pk)
                username = request.POST.get('username', '')
                username = username.replace(",", " ")
                username = username.replace(";", " ")
                username = username.replace(".", " ")
                users = username.split()

                for name in users:
                    try:
                        user = User.objects.get(username=name)
                        instance.secondary_user.add(user)
                    except:
                        messages.add_message(request, messages.ERROR,
                                             'Error. The user name you entered'
                                             ', ' + name + ', does not exist.')
                        return redirect('contour:index')
                    else:
                        instance.save()
                return redirect(redirection)
            else:
                return render(request, template, {'form': forms.SecUserForm})

    @staticmethod
    @abstractmethod
    def add(request, *args):
        """
       The method adds an item to a certain Model (database).
       :param request:     to add an item to the model. 
       :return:            different HttpResponses. Success: redirect
       to a certain model overview, Fault: return info
                           about wrong input.
       """

    @staticmethod
    @abstractmethod
    def select(request):
        """
        The method returns a HttpResponse where you can select a File
        from a Model to do further calculations.
        :return:        HttpResponse to select an item form a certain model. 
        """

    @staticmethod
    def show(request, pk, model):
        """
        Shows an object from the data base, e.g. an EnvironmentalContour object.

        Parameters
        ----------
        request : HttpRequest,
            The HttpRequest to show the object.
        pk : int,
            Primary key of the object in the data base.
        model : models.Model,
            A Django model, which has a database associated to it, e.g.
            models.EnvronmentalContour. This is the class, not an instance.


        Returns
        -------
        response : HttpResponse,
            Renders an html response showing the object.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect(reverse('contour:index'))
        else:
            html = 'contour/' + model.url_str() + '_show.html'
            object = model.objects.get(pk=pk)
            return render(request, html, {'object': object})


class MeasureFileHandler(Handler):
    @staticmethod
    def overview(request, collection=MeasureFileModel):
        return Handler.overview(request, collection)

    @staticmethod
    def delete(request, pk, collection=MeasureFileModel):
        return Handler.delete(request, pk, collection)

    @staticmethod
    def update(request, pk, collection=MeasureFileModel):
        return Handler.update(request, pk, collection)

    @staticmethod
    def select(request):
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            collection = MeasureFileModel
            meas = collection.objects.all()
            context = set()
            for item in meas:
                bool_ = False
                for secUser in item.secondary_user.all():
                    if secUser == request.user:
                        bool_ = True
                if bool_:
                    context.add(item)
                elif item.primary_user == request.user:
                    context.add(item)

            return render(request,
                          'contour/measure_file_model_select.html',
                          {'context': context}
                          )

    @staticmethod
    def add(request):
        """
        The method adds an item to MeasureFile 
        :return: 
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            measure_file_form = forms.MeasureFileForm()
            if request.method == 'POST':
                measure_file_form = forms.MeasureFileForm(
                    data=request.POST,
                    files=request.FILES
                )
                if measure_file_form.is_valid():
                    measure_model = MeasureFileModel(
                        primary_user=request.user,
                        title=measure_file_form.cleaned_data['title']
                    )
                    measure_model.save()
                    measure_model.measure_file.save(
                        measure_file_form.cleaned_data['measure_file'].name,
                        measure_file_form.cleaned_data['measure_file'].file
                    )
                    measure_model.save()
                    path = settings.PATH_MEDIA + \
                           settings.PATH_USER_GENERATED + \
                           str(request.user) + \
                           '/measurement/' + str(measure_model.pk)
                    measure_model.path_of_statics = path
                    measure_model.save(
                        update_fields=['path_of_statics'])

                    return redirect(
                        'contour:measure_file_model_plot',
                        measure_model.pk
                    )
                else:
                    return render(
                        request,
                        'contour/measure_file_model_add.html',
                        {'form': measure_file_form}
                    )
            else:
                return render(
                    request,
                    'contour/measure_file_model_add.html',
                    {'form': measure_file_form}
                )

    @staticmethod
    def fit_file(request, pk):
        """
        The method fits a MeasureFile item and shows the result. If the fit
        isn't possible the user is going to be
        informed with an error message.
        :return:        HttpResponse.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            mfm_item = MeasureFileModel.objects.get(pk=pk)
            var_names, var_symbols = get_info_from_file(mfm_item.measure_file.url)
            var_number = len(var_names)
            fit_form = forms.MeasureFileFitForm(
                variable_count=var_number,
                variable_names=var_names
            )
            if request.method == 'POST':
                fit_form = forms.MeasureFileFitForm(
                    data=request.POST,
                    variable_count=var_number,
                    variable_names=var_names
                )
                if fit_form.is_valid():
                    ci = ComputeInterface()
                    try:
                        fit = ci.fit_curves(mfm_item=mfm_item,
                                            fit_settings=fit_form.cleaned_data,
                                            var_number=var_number
                                            )
                    except (ValueError, RuntimeError, IndexError, TypeError,
                            NameError, KeyError, Exception) as err:
                        return render(
                            request,
                            'contour/error.html',
                            {'error_message': err,
                             'text': FITTING_ERROR_MSG,
                               'header': 'Fit measurement file to probabilistic '
                                         'model',
                               'return_url': 'contour:measure_file_model_select'
                             }
                        )
                    directory_prefix = settings.PATH_MEDIA
                    directory_after_static = settings.PATH_USER_GENERATED + \
                                             str(request.user) + '/prob_model/'
                    directory = directory_prefix + directory_after_static
                    prob_model = save_fitted_prob_model(fit,
                                                        fit_form.cleaned_data[
                                                            'title'],
                                                        var_names,
                                                        var_symbols,
                                                        request.user,
                                                        mfm_item)
                    plot.plot_fit(fit, var_names, var_symbols, directory,
                                  prob_model)
                    multivariate_distribution = plot.setup_mul_dist(
                        prob_model
                    )
                    latex_string_list = multivariate_distribution.latex_repr(
                        var_symbols
                    )
                    sorted_figures = plot.sort_plotted_figures(prob_model)
                    return render(request,
                                  'contour/fit_results.html',
                                  {'pk': prob_model.pk,
                                   'sorted_figures': sorted_figures,
                                   'latex_string_list': latex_string_list
                                   }
                                  )
                else:
                    return render(request,
                                  'contour/measure_file_model_fit.html',
                                  {'form': fit_form}
                                  )
            return render(request,
                          'contour/measure_file_model_fit.html',
                          {'form': fit_form}
                          )


    @staticmethod
    def new_fit(request, pk):
        """
        The method deletes the previous fit and returns the form to enter a new
        fit.
        :param request: to make a new fit.
        :param pk:      primary key of the previous fit. 
        :return:        HttpResponse to enter a new fit.     
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            plot.ProbabilisticModel.objects.all().filter(pk=pk).delete()
            user_files = MeasureFileModel.objects.all().filter(
                primary_user=request.user
            )
            return render(request,
                          'contour/measure_file_model_select.html',
                          {'context': user_files}
                          )

    @staticmethod
    def plot_file(request, pk):
        """
        The method plots a MeasureFile
        :return:        HttpResponse.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            measure_file_model = MeasureFileModel.objects.get(pk=pk)
            var_names, var_symbols = get_info_from_file(
                measure_file_model.measure_file.url
            )
            directory_prefix = settings.PATH_MEDIA
            directory_after_static = settings.PATH_USER_GENERATED + \
                                     str(request.user) + \
                                     '/measurement/' + str(pk)
            plot.plot_data_set_as_scatter(request.user,
                                          measure_file_model,
                                          var_names)
            return render(request,
                          'contour/measure_file_model_plot.html',
                          {'user': request.user,
                           'measure_file_model':measure_file_model,
                           'directory': directory_after_static}
                          )


class ProbabilisticModelHandler(Handler):
    @staticmethod
    def overview(request, collection=models.ProbabilisticModel):
        return Handler.overview(request, collection)

    @staticmethod
    def delete(request, pk, collection=models.ProbabilisticModel):
        return Handler.delete(request, pk, collection)

    @staticmethod
    def update(request, pk, collection=models.ProbabilisticModel):
        return Handler.update(request, pk, collection)

    @staticmethod
    def select(request):
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            user_pm = models.ProbabilisticModel.objects.all().filter(
                primary_user=request.user
            )
            return render(request,
                          'contour/probabilistic_model_select.html',
                          {'context': user_pm}
                          )

    @staticmethod
    def add(request, *args):
        """
        The method adds an item to the ProbabilisticModel (database).
        :param request:     to add an item to the model. 
        :param var_num:     number of variables which should be added to
        the model.
        :return:            different HttpResponses. Success: redirect to
        select probabilistic model, Fault: return info
                            about wrong input.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            var_num = args[0]
            var_num_int = int(var_num)
            variable_form = forms.VariablesForm(variable_count=var_num_int)
            var_num_form = forms.VariableNumber()
            if request.method == 'POST':
                variable_form = forms.VariablesForm(data=request.POST,
                                                    variable_count=var_num_int)
                if variable_form.is_valid():
                    is_valid_probabilistic_model = True
                    probabilistic_model = models.ProbabilisticModel(
                        primary_user=request.user,
                        collection_name=variable_form.cleaned_data[
                            'collection_name'],
                        measure_file_model=None)
                    probabilistic_model.save()
                    for i in range(var_num_int):
                        distribution = models.DistributionModel(
                            name=variable_form.cleaned_data[
                                'variable_name_' + str(i)
                            ],
                            distribution=variable_form.cleaned_data[
                                'distribution_' + str(i)
                            ],
                            symbol=variable_form.cleaned_data[
                                'variable_symbol_' + str(i)
                            ],
                            probabilistic_model=probabilistic_model
                        )
                        distribution.save()
                        params = ['shape', 'location', 'scale']
                        if i == 0:
                            for param in params:
                                parameter = models.ParameterModel(
                                    function='None',
                                    x0=variable_form.cleaned_data[
                                        param + '_' + str(i) + '_0'
                                    ],
                                    dependency='!',
                                    name=param,
                                    distribution=distribution
                                )
                                try:
                                    parameter.clean()
                                except ValidationError as e:
                                    messages.add_message(request,
                                                         messages.ERROR,
                                                         e.message)
                                    is_valid_probabilistic_model = False
                                else:
                                    parameter.save()

                        else:
                            for param in params:
                                parameter = models.ParameterModel(
                                    function=variable_form.cleaned_data[param + '_dependency_' + str(i)][1:],
                                    x0=variable_form.cleaned_data[param + '_' + str(i) + '_0'],
                                    x1=variable_form.cleaned_data[param + '_' + str(i) + '_1'],
                                    x2=variable_form.cleaned_data[param + '_' + str(i) + '_2'],
                                    dependency=variable_form.cleaned_data[param + '_dependency_' + str(i)][0],
                                    name=param, distribution=distribution)
                                try:
                                    parameter.clean()
                                except ValidationError as e:
                                    messages.add_message(
                                        request,
                                        messages.ERROR,
                                        e.message
                                    )
                                    is_valid_probabilistic_model = False
                                else:
                                    parameter.save()
                    if is_valid_probabilistic_model:
                        return redirect('contour:probabilistic_model_select')
                    else:
                        probabilistic_model.delete()
                        return render(request,
                                      'contour/probabilistic_model_add.html',
                                      {'form': variable_form,
                                       'var_num_form': var_num_form})
                else:
                    return render(request,
                                  'contour/probabilistic_model_add.html',
                                  {'form': variable_form,
                                   'var_num_form': var_num_form})

            return render(request, 'contour/probabilistic_model_add.html',
                          {'form': variable_form, 'var_num_form': var_num_form})

    @staticmethod
    def calculate(request, pk, method):
        """
        The method handles the calculation requests and calls the specific calculation method iform_calc or hdc_calc.
        :param request:     user request to calculate a function. 
        :param pk:          primary key of item of the ProbabilisticModel database.
        :param method:      the calculation method. 'I' = iform_calc, 'H' = hdc_calc.
        :return:            a graph with table (pdf) or error message.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            item = models.ProbabilisticModel.objects.get(pk=pk)
            var_names = []
            var_symbols = []
            dists_model = models.DistributionModel.objects.filter(
                probabilistic_model=item
            )

            for dist in dists_model:
                var_names.append(dist.name)
                var_symbols.append(dist.symbol)
            if method == 'I':
                return ProbabilisticModelHandler.iform_calc(
                    request,
                    var_names,
                    var_symbols,
                    item
                )
            elif method == 'H':
                return ProbabilisticModelHandler.hdc_calc(
                    request,
                    var_names,
                    var_symbols,
                    item
                )
            else:
                KeyError('{} no matching calculation method')

    @staticmethod
    def iform_calc(request, var_names, var_symbols, probabilistic_model):
        """
        Calls the IFORM contour calculation and handles errors if they occur.

        Parameters
        ----------
        request : HttpRequest,
            The HttpRequest to either show the calculation settings page or to
            calculate the contour (differentiated by POST or GET request).
        var_names : list of str
            Names of the variables.
        var_symbols : list of str
            Names of the symbols of the probabilistic model's variables.
        probabilistic_model : models.ProbabilisticModel
            Probabilistic model, which should be used for the environmental
            contour calculation.

        Returns
        -------
        response : HttpResponse,
            Renders an html response showing contour or the error message.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            iform_form = forms.IFormForm()
            cs = ComputeInterface
            if request.method == 'POST':
                iform_form = forms.IFormForm(data=request.POST)
                if iform_form.is_valid():
                    try:
                        with warnings.catch_warnings(record=True) as warn:
                            contour_coordinates = cs.iform(
                                probabilistic_model,
                                float(iform_form.cleaned_data['return_period']),
                                float(iform_form.cleaned_data['sea_state']),
                                iform_form.cleaned_data['n_steps'])
                            validate_contour_coordinates(contour_coordinates)
                            environmental_contour = EnvironmentalContour(
                                primary_user=request.user,
                                fitting_method="",
                                contour_method="Inverse first order reliability "
                                               "method (IFORM)",
                                return_period=float(
                                    iform_form.cleaned_data['return_period']),
                                state_duration=float(
                                    iform_form.cleaned_data['sea_state']),
                                probabilistic_model=probabilistic_model
                            )
                            # Save the environmental contour here that it gets
                            # a primary key.
                            environmental_contour.save()
                            additional_contour_options = []
                            additional_contour_option = AdditionalContourOption(
                                option_key="Number of points on the contour",
                                option_value=iform_form.cleaned_data['n_steps'],
                                environmental_contour=environmental_contour
                            )
                            additional_contour_options.append(
                                additional_contour_option)
                            save_environmental_contour(
                                environmental_contour,
                                additional_contour_options,
                                contour_coordinates,
                                str(request.user))
                    # Catch and allocate errors caused by calculating iform.
                    except (ValidationError, RuntimeError, IndexError, TypeError,
                            NameError, KeyError, Exception) as err:
                        return render(
                            request,
                            'contour/error.html',
                            {'error_message': err,
                             'text': CONTOUR_CALCULATION_ERROR_MSG,
                             'header': 'Calculate contour',
                             'return_url': 'contour:probabilistic_model_select'})
                    try:
                        plot.create_latex_report(contour_coordinates,
                                                 str(request.user),
                                                 environmental_contour,
                                                 var_names,
                                                 var_symbols)
                    except (ValueError) as err:
                        return render(
                            request,
                            'contour/error.html',
                            {'error_message': err,
                             'text': CONTOUR_REPORT_ERROR_MSG,
                             'header': 'Report of the contour',
                             'return_url': 'contour:probabilistic_model_select'}
                        )
                    response = ProbabilisticModelHandler.render_calculated_contour(
                        request, environmental_contour, contour_coordinates,
                        probabilistic_model, warn)
                    return response
                else:
                    return render(request,
                                  'contour/contour_settings.html',
                                  {'form': iform_form}
                                  )
            else:
                return render(request,
                              'contour/contour_settings.html',
                              {'form': iform_form}
                              )

    @staticmethod
    def hdc_calc(request, var_names, var_symbols, probabilistic_model):
        """
        Calls the HDC calculation and handles errors if they occur.

        Parameters
        ----------
        request : HttpRequest,
            The HttpRequest to either show the calculation settings page or to
            calculate the contour (differentiated by POST or GET request).
        var_names : list of str
            Names of the variables.
        var_symbols : list of str
            Names of the symbols of the probabilistic model's variables.
        probabilistic_model : models.ProbabilisticModel
            Probabilistic model, which should be used for the environmental
            contour calculation.

        Returns
        -------
        response : HttpResponse,
            Renders an html response showing contour or the error message.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            hdc_form = forms.HDCForm(var_names=var_names)
            cs = ComputeInterface()
            if request.method == 'POST':
                hdc_form = forms.HDCForm(data=request.POST, var_names=var_names)
                if hdc_form.is_valid():
                    limits = []
                    deltas = []
                    warn = None
                    contour_coordinates = None
                    for i in range(len(var_names)):
                        limits.append(
                            (float(hdc_form.cleaned_data['limit_%s' % i + '_1']),
                             float(hdc_form.cleaned_data['limit_%s' % i + '_2'])))
                        deltas.append(float(hdc_form.cleaned_data['delta_%s' % i]))
                    try:
                        with warnings.catch_warnings(record=True) as warn:
                            contour_coordinates = cs.hdc(
                                probabilistic_model,
                                float(hdc_form.cleaned_data['n_years']),
                                float(hdc_form.cleaned_data['sea_state']),
                                limits, deltas)
                            validate_contour_coordinates(contour_coordinates)
                            environmental_contour = EnvironmentalContour(
                                primary_user=request.user,
                                fitting_method="",
                                contour_method="Highest density contour (HDC) "
                                               "method",
                                return_period=float(
                                    hdc_form.cleaned_data['n_years']),
                                state_duration=float(
                                    hdc_form.cleaned_data['sea_state']),
                                probabilistic_model=probabilistic_model
                            )
                            # Save the environmental contour here that it gets
                            # a primary key.
                            environmental_contour.save()
                            additional_contour_options = []
                            additional_contour_option = AdditionalContourOption(
                                option_key="Limits of the grid",
                                option_value=" ".join(map(str, limits)),
                                environmental_contour=environmental_contour
                            )
                            additional_contour_options.append(
                                additional_contour_option)
                            additional_contour_option = AdditionalContourOption(
                                option_key="Grid cell size ($\Delta x_i$)",
                                option_value=" ".join(map(str, deltas)),
                                environmental_contour=environmental_contour
                            )
                            additional_contour_options.append(
                                additional_contour_option)
                            save_environmental_contour(
                                environmental_contour,
                                additional_contour_options,
                                contour_coordinates,
                                str(request.user))
                    # Catch and allocate errors caused by calculating a HDC.
                    except (TimeoutError, ValidationError, RuntimeError,
                            IndexError, TypeError, NameError, KeyError) as err:
                        return render(
                            request,
                            'contour/error.html',
                            {'error_message': err,
                             'text': CONTOUR_CALCULATION_ERROR_MSG,
                             'header': 'Calculate contour',
                             'return_url': 'contour:probabilistic_model_select'}
                        )

                    try:
                        plot.create_latex_report(contour_coordinates,
                                                 str(request.user),
                                                 environmental_contour,
                                                 var_names,
                                                 var_symbols)
                    except (ValueError) as err:
                        return render(
                            request,
                            'contour/error.html',
                            {'error_message': err,
                             'text': CONTOUR_REPORT_ERROR_MSG,
                             'header': 'Report of the contour',
                             'return_url': 'contour:probabilistic_model_select'}
                        )
                    response = ProbabilisticModelHandler.render_calculated_contour(
                        request, environmental_contour, contour_coordinates,
                        probabilistic_model, warn)
                    return response
                else:
                    return render(request, 'contour/contour_settings.html',
                                  {'form': hdc_form}
                                  )
            else:
                return render(request, 'contour/contour_settings.html',
                              {'form': hdc_form}
                              )

    @staticmethod
    def render_calculated_contour(request, environmental_contour,
                                  contour_coordinates, probabilistic_model,
                                  warn):
        """

        Parameters
        ----------
        request : HttpRequest,
            The HttpRequest to calculate the contour. It is a POST request.
        environmental_contour : EnvironmentalContour,
            The EnvironmentalContour that just got computed.
        contour_coordinates : list of list of np.ndarray,
            The contour's coordinates.
            The format is defined in viroconcom.contours.Contour.
        probabilistic_model : ProbabilisticModel,
            The ProbabilisticModel, which was used to calculate the
            EnvironmentalContour
        warn : list of warning,
            Warnings can get raised during the calculation of the contour.
            Then the user will be presented these warnings.

        Returns
        -------
        response : HttpResponse,
            The rendered template 'evnironmental_contour_show.html' with the
            calculated EnvironmentalContour.
        """
        # If the probabilistic model is 4-dimensional send data to create a 4D
        # interactive plot.
        if len(contour_coordinates[0]) == 4:
            dists = models.DistributionModel.objects.filter(
                probabilistic_model=probabilistic_model
            )
            labels = []
            for dist in dists:
                labels.append('{} [{}]'.format(dist.name, dist.symbol))
            response = render(request,
                          'contour/environmental_contour_show.html',
                          {'object': environmental_contour,
                           'x': contour_coordinates[0][0].tolist(),
                           'y': contour_coordinates[0][1].tolist(),
                           'z': contour_coordinates[0][2].tolist(),
                           'u': contour_coordinates[0][3].tolist(),
                           'dim': 4,
                           'labels': labels}
                          )
        # If the probabilistic model is 3-dimensional send data for a 3D
        # interactive plot
        elif len(contour_coordinates[0]) == 3:
            dists = models.DistributionModel.objects.filter(
                probabilistic_model=probabilistic_model
            )
            labels = []
            for dist in dists:
                labels.append('{} [{}]'.format(dist.name, dist.symbol))
            response = render(request,
                          'contour/environmental_contour_show.html',
                          {'object': environmental_contour,
                           'x': contour_coordinates[0][0].tolist(),
                           'y': contour_coordinates[0][1].tolist(),
                           'z': contour_coordinates[0][2].tolist(),
                           'dim': 3,
                           'labels': labels})

        elif len(contour_coordinates) < 3:
            response = render(request,
                          'contour/environmental_contour_show.html',
                          {'object': environmental_contour, 'dim': 2}
                          )
        return response



    @staticmethod
    def set_variables_number(request):
        """
        The method sets the variable number in the VariablesForm
        :param request:     user request to change the variable number 
        :return:            a VariablesForm with the certain variable number 
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            var_num_str = str()
            if request.method == 'POST':
                var_num_form = forms.VariableNumber(request.POST)
                if var_num_form.is_valid():
                    var_num = var_num_form.cleaned_data['variable_number']
                    var_num_str = str(var_num)
                    if int(var_num) < 10:
                        var_num_str = '0' + var_num_str
                return redirect('contour:probabilistic_model_add', var_num_str)
            else:
                variable_form = forms.VariablesForm()
                var_num_form = forms.VariableNumber()
                return render(request, 'contour/probabilistic_model_add.html',
                              {'form': variable_form, 'var_num_form': var_num_form})

    @staticmethod
    def show_model(request, pk):
        """
        The method shows a probabilistic model (name, equation of the joint pdf,
        information about the fit)
        :return:        HttpResponse.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            probabilistic_model = models.ProbabilisticModel.objects.get(pk=pk)
            dists_model = models.DistributionModel.objects.filter(
                probabilistic_model=probabilistic_model
            )
            var_symbols = []
            for dist in dists_model:
                var_symbols.append(dist.symbol)
            multivariate_distribution = plot.setup_mul_dist(probabilistic_model)
            latex_string_list = multivariate_distribution.latex_repr(var_symbols)

            sorted_figures = plot.sort_plotted_figures(probabilistic_model)

            return render(
                request,
                'contour/probabilistic_model_show.html',
                {'user': request.user,
                 'probabilistic_model': probabilistic_model,
                 'latex_string_list': latex_string_list,
                 'sorted_figures': sorted_figures})


class EnvironmentalContourHandler(Handler):
    """
    Handler for EnvironmentalContour objects
    """

    @staticmethod
    def overview(request, collection=models.EnvironmentalContour):
        return Handler.overview(request, collection)

    @staticmethod
    def delete(request, pk, collection=models.EnvironmentalContour):
        return Handler.delete(request, pk, collection)

    @staticmethod
    def update(request, pk, collection=models.EnvironmentalContour):
        return Handler.update(request, pk, collection)

    @staticmethod
    def show(request, pk, model=models.EnvironmentalContour):
        return Handler.show(request, pk, model)

    @staticmethod
    def delete(request, pk, collection=models.EnvironmentalContour):
        return Handler.delete(request, pk, collection)


def save_fitted_prob_model(fit, model_title, var_names, var_symbols, user,
                           measure_file):
    """
    Saves a probabilistic model which was fitted to measurement data.

    Parameters
    ----------
    fit : Fit
        Calculated fit results of a measurement file.
    model_title : str
        Title of the probabilistic model.
    var_names : list of str
        Names of the variables.
    var_symbols : list of str
        Names of the symbols of the probabilistic model's variables.
    user : str
        Name of a user.
    measure_file : MeasureFileModel
        MeasureFileModel object linked to the probabilistic model.

    Returns
    -------
    ProbabilisticModel
        Which was fitted to measurement data

    """
    probabilistic_model = ProbabilisticModel(primary_user=user,
                                             collection_name=model_title,
                                             measure_file_model=measure_file)
    probabilistic_model.save()

    for i, dist in enumerate(fit.mul_var_dist.distributions):
        if dist.name == 'Lognormal':
            dist_name = "Lognormal_2"

            distribution_model = DistributionModel(name=var_names[i],
                                                   symbol=var_symbols[i],
                                                   probabilistic_model=probabilistic_model,
                                                   distribution=dist_name)
            distribution_model.save()
            save_parameter(dist.shape, distribution_model,
                           fit.mul_var_dist.dependencies[i][0], 'shape')
            save_parameter(dist.loc, distribution_model,
                           fit.mul_var_dist.dependencies[i][1], 'loc')
            save_parameter(dist.mu, distribution_model,
                           fit.mul_var_dist.dependencies[i][2], 'scale')
        else:
            distribution_model = DistributionModel(name=var_names[i],
                                                   symbol=var_symbols[i],
                                                    probabilistic_model=probabilistic_model,
                                                   distribution=dist.name)
            distribution_model.save()
            save_parameter(dist.shape, distribution_model,
                           fit.mul_var_dist.dependencies[i][0], 'shape')
            save_parameter(dist.loc, distribution_model,
                           fit.mul_var_dist.dependencies[i][1], 'loc')
            save_parameter(dist.scale, distribution_model,
                           fit.mul_var_dist.dependencies[i][2], 'scale')

    return probabilistic_model


def save_environmental_contour(environmental_contour,
                           additional_contour_options,
                           contour_coordinates,
                           user):
    """
    Saves an EnvironmentalContour object and its depending models to the data
    base.


    Parameters
    ----------
    environmental_contour : EnvironmentalContour,
        The environmental contour obect that should be saved.
    additional_contour_options : list of AdditionalContourOption,
        Options, whch are specific to the contour and are not general
        environmental contour options.
    contour_coordinates : list of list of numpy.ndarray,
        Contains the coordinates of points on the contour.
        The outer list contains can hold multiple contour paths if the
        distribution is multimodal. The inner list contains multiple
        numpy arrays of the same length, one per dimension.
        The values of the arrays are the coordinates in the corresponding
        dimension.
    user : str,
        The user who should own the environmental contour.

    Returns
    -------

    """
    # Only save the object if it has not been saved yet.
    if environmental_contour.pk is None:
        environmental_contour.save()
    path = settings.PATH_MEDIA + \
           settings.PATH_USER_GENERATED + \
           user + \
           '/contour/' + str(environmental_contour.pk)
    environmental_contour.path_of_statics = path
    environmental_contour.save(
        update_fields=['path_of_statics'])
    for additional_contour_option in additional_contour_options:
        # It is necessary to create a new AdditionalContourObject because the
        # original object was created with an environmental contour, which has
        # been saved yet and consequently does not have a primary key.
        additional_contour_option_w_pk = AdditionalContourOption(
            option_key=additional_contour_option.option_key,
            option_value=additional_contour_option.option_value,
            environmental_contour=environmental_contour)
        additional_contour_option_w_pk.save()
    # Saving all coordinates to the database is slow since a lot of operations
    # might be necessary. Consequenetly, this can be turned off.
    if DO_SAVE_CONTOUR_COORDINATES_IN_DB:
        for i in range(len(contour_coordinates)):
            contour_path = ContourPath(
                environmental_contour=environmental_contour)
            contour_path.save()
            for j in range(len(contour_coordinates[i])):
                EEDC = ExtremeEnvDesignCondition(
                    contour_path=contour_path)
                EEDC.save()
                for k in range(len(contour_coordinates[i][j])):
                    eedc_scalar = EEDCScalar(
                        x=float(contour_coordinates[i][j][k]),
                        EEDC=EEDC)
                    eedc_scalar.save()
    return environmental_contour


def save_parameter(parameter, distribution_model, dependency, name):
    """
    Saves a fitted parameter and links it to a DistributionModel.

    Parameters
    ----------
    parameter : ConstantParam or FunctionParam
        ConstantParam is a float value. FunctionParam contains a whole function
        like power function or exponential.
    distribution_model : DistributionModel
        The parameter will be linked to this DistributionModel.
    dependency : int
        The dimension the dependency is based on.
    name : str
        Name of the parameter ('shape', 'loc' or 'scale')
    """
    if type(parameter) == params.ConstantParam:
        parameter_model = ParameterModel(function='None',
                                         x0=parameter(0),
                                         dependency='!',
                                         distribution=distribution_model,
                                         name=name)
        parameter_model.save()
    elif type(parameter) == params.FunctionParam:
        parameter_model = ParameterModel(function=parameter.func_name,
                                         x0=parameter.a,
                                         x1=parameter.b,
                                         x2=parameter.c,
                                         dependency=dependency,
                                         distribution=distribution_model,
                                         name=name)
        parameter_model.save()
    else:
        parameter_model = ParameterModel(function='None',
                                         x0=0,
                                         dependency='!',
                                         distribution=distribution_model,
                                         name=name)
        parameter_model.save()


def get_info_from_file(url):
    """	
    Reads the variable names and symbols form a csv. file.
    
    Parameters
    ----------
    url : str
        Path to the csv file.

    Returns
    -------
    var_names : list of strings
        Names of the environmental variables used in csv file,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']
    var_symbols : list of strings
        Symbols of the environental variables used in the csv file,
        e.g. ['V', 'Hs']
    """
    if url[0] == '/':
        url = url[1:]
    if url[0:8] == 'https://':
        req = request.Request(url)
        print('Trying to urlopen the url: ' + str(url))
        with request.urlopen(req) as response:
            reader = csv.reader(codecs.iterdecode(response, 'utf-8'), delimiter=';').__next__()
            var_names, var_symbols = get_info_from_reader(reader)
    else:
        with open(url, 'r') as file:
            reader = csv.reader(file, delimiter=';').__next__()
            var_names, var_symbols = get_info_from_reader(reader)

    return var_names, var_symbols


def get_info_from_reader(reader):
    """
    Reads the variable names and symbols form a reader

    Parameters
    ----------
    reader : csv.Reader
        A Reader object that can read a file line by line.
        See https://docs.python.org/2/library/csv.html#reader-objects for
        a proper documentation.

    Returns
    -------
    var_names : list of strings
        Names of the environmental variables used in csv file,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']
    var_symbols : list of strings
        Symbols of the environental variables used in the csv file,
        e.g. ['V', 'Hs']
    """
    var_names = []
    var_symbols = []
    i = 0
    while i < (len(reader)):
        var_names.append(reader[i])
        i += 1
        var_symbols.append(reader[i])
        i += 1
    return var_names, var_symbols