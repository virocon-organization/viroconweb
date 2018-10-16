"""
Handles requests and outputs rendered html.
"""
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
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.urls import reverse
from multiprocessing import TimeoutError
from urllib import request
from abc import abstractmethod

from . import forms
from . import models
from . import plot
from . import settings

from viroconweb.settings import RUN_MODE
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
FITTING_ERROR_MSG = 'Feel free to contact us if you ' \
                    'think this error is caused by a bug: ' \
                    'virocon@uni-bremen.de'



def index(request):
    """
    Renders the landing page, i.e. the 'Dashboard'.
    """
    return render(request, 'contour/home.html')


class Handler:
    @staticmethod
    def overview(request, model_class):
        """
        Renders an overview about all objects of a Django Model (all data base
        entries).

        Parameters
        ----------
        request : HttpRequest,
            Request to show the overview.
        model_class : class of models.Model,
            The class of a Django Model as defined in models.py, e.g.
            MeasurementFileModel or EnvironmentalContour.

        Returns
        -------
        HttpResponse,
            The rendered overview.
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            objects = model_class.objects.all()
            context = set()
            for object in objects:
                bool_ = False
                for secUser in object.secondary_user.all():
                    if secUser == request.user:
                        bool_ = True
                if bool_:
                    context.add(object)
                elif object.primary_user == request.user:
                    context.add(object)

            base = 'contour:' + model_class.url_str()
            html = 'contour/' + model_class.url_str() + '_overview.html'
            update = base + '_update'
            delete = base + '_delete'
            add = base + '_add'
            calc = base + '_calc'

            return render(request, html, {'context': context,
                                          'name': model_class,
                                          'update': update,
                                          'delete': delete,
                                          'add': add,
                                          'calc': calc})

    @staticmethod
    def delete(request, pk, model_class):
        """
        Deletes an object from the data base.

        Parameters
        ----------
        request : HttpRequest,
            The request to delete the object.
        pk : int,
            The object's primary key.
        model_class: class of models.Model,
            The class of the Django Model (as defined in models.py).
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            object = get_object_or_404(model_class, pk=pk)
            if hasattr(object, 'primary_user'):
                if object.primary_user == request.user:
                    object.delete()
                else:
                    object.secondary_user.remove(request.user)
            else:
                object.delete()
            redirection = 'contour:' + model_class.url_str() + '_overview'
            return redirect(redirection)

    @staticmethod
    def update(request, pk, model_class):
        """
        Updates an object in the data base.

        Parameters
        ----------
        request : HttpRequest,
            The request to update the object.
        pk : int,
            The object's primary key.
        model_class: class of models.Model,
            The class of the Django Model (as defined in models.py).
        """
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            redirection = 'contour:' + model_class.url_str() + '_overview'
            template = 'contour/update_sec_user.html'
            if request.method == 'POST':
                object = get_object_or_404(model_class, pk=pk)
                username = request.POST.get('username', '')
                username = username.replace(",", " ")
                username = username.replace(";", " ")
                username = username.replace(".", " ")
                users = username.split()

                for name in users:
                    try:
                        user = User.objects.get(username=name)
                        object.secondary_user.add(user)
                    except:
                        messages.add_message(request, messages.ERROR,
                                             'Error. The user name you entered'
                                             ', ' + name + ', does not exist.')
                        return redirect('contour:index')
                    else:
                        object.save()
                return redirect(redirection)
            else:
                return render(request, template, {'form': forms.SecUserForm})

    @staticmethod
    @abstractmethod
    def add(request, *args):
        """
        Adds an object to the data base.

        Must be overwritten by the Handler specific to one Django Model.

        Parameters
        ----------
        request : HttpRequest,
            The request to add the object to the data base.
        """

    @staticmethod
    @abstractmethod
    def select(request):
        """
        A reduced overview of all objects to guide the user through the work
        flow shown at the Dashboard.

        Parameters
        ----------
        request : HttpRequest,
            Request to render the select view.

        Returns
        -------

        """

    @staticmethod
    def show(request, pk, model_class):
        """
        Shows an object from the data base, e.g. an EnvironmentalContour object.

        Parameters
        ----------
        request : HttpRequest,
            The HttpRequest to show the object.
        pk : int,
            Primary key of the object in the data base.
        model_class : models.Model,
            The class of the Django model, which should be shown. For example
            the class models.EnvronmentalContour.


        Returns
        -------
        response : HttpResponse,
            Renders an html response showing the object.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect(reverse('contour:index'))
        else:
            html = 'contour/' + model_class.url_str() + '_show.html'
            object = model_class.objects.get(pk=pk)
            return render(request, html, {'object': object})


class MeasureFileHandler(Handler):
    @staticmethod
    def overview(request, model_class=MeasureFileModel):
        return Handler.overview(request, model_class)

    @staticmethod
    def delete(request, pk, model_class=MeasureFileModel):
        return Handler.delete(request, pk, model_class)

    @staticmethod
    def update(request, pk, model_class=MeasureFileModel):
        return Handler.update(request, pk, model_class)

    @staticmethod
    def select(request):
        if request.user.is_anonymous:
            return redirect('contour:index')
        else:
            model_class = MeasureFileModel
            objects = model_class.objects.all()
            context = set()
            for object in objects:
                bool_ = False
                for secUser in object.secondary_user.all():
                    if secUser == request.user:
                        bool_ = True
                if bool_:
                    context.add(object)
                elif object.primary_user == request.user:
                    context.add(object)

            return render(request,
                          'contour/measure_file_model_select.html',
                          {'context': context}
                          )

    @staticmethod
    def add(request):
        """
        Adds a MeasurementFileModel to the data base.

        Parameters
        ----------
        request : HttpRequest,
            Request to add the model to the data base.

        Returns
        -------
        HttpResponse,
            Renders the a response to the user after she/he added the model.
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
        Fits a probabilistic model to a measurement file and renders the result.

        Parameters
        ----------
        request : HttpRequest,
            Request to peform a fit.
        pk : int,
            Primary key of the measurement file.

        Returns
        -------
        HttpResponse,
            Renders the fitting result.
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
                            NameError, KeyError, TimeoutError) as err:
                        if RUN_MODE == 'production' and err.__class__.__name__ == 'TimeoutError':
                            fitting_error_message = \
                                '<p>Consider running a copy of ViroCon locally ' \
                                'to allow a longer computation time. See the ' \
                                'instruction at <a href="https://github.com/' \
                                'virocon-organization/viroconweb#how-to-use-virocon">' \
                                'https://github.com/' \
                                'virocon-organization/viroconweb#how-to-use-virocon' \
                                '</a> on ' \
                                'how to do that.</p>' + FITTING_ERROR_MSG
                        else:
                            fitting_error_message = FITTING_ERROR_MSG
                        return render(
                            request,
                            'contour/error.html',
                            {'error_message': err,
                             'text': fitting_error_message,
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
                    figure_collections = plot.sort_plotted_figures(prob_model)
                    return render(request,
                                  'contour/fit_results.html',
                                  {'pk': prob_model.pk,
                                   'figure_collections': figure_collections,
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
        Deletes the previous fit and returns the form to define a new fit.

        Parameters
        ----------
        request : HttpRequest,
            Request to perform a new fit.
        pk : int,
            Primary key of the previous fit, which will be deleted.

        Returns
        -------
        HttpResponse,
            Renders the view to select a measurement file for fitting.
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
        Plots and renders a measurement file.

        Parameters
        ----------
        request : HttpRequest,
            Request to plot a measurement file.
        pk : int,
            Primary key of the measurement file, which will be plotted.

        Returns
        -------
        HttpResponse,
            Renders the plotted measurement file.
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
            plot.plot_data_set_as_scatter(measure_file_model, var_names)
            return render(request,
                          'contour/measure_file_model_plot.html',
                          {'user': request.user,
                           'measure_file_model':measure_file_model,
                           'directory': directory_after_static}
                          )


class ProbabilisticModelHandler(Handler):
    @staticmethod
    def overview(request, model_class=models.ProbabilisticModel):
        return Handler.overview(request, model_class)

    @staticmethod
    def delete(request, pk, model_class=models.ProbabilisticModel):
        return Handler.delete(request, pk, model_class)

    @staticmethod
    def update(request, pk, model_class=models.ProbabilisticModel):
        return Handler.update(request, pk, model_class)

    @staticmethod
    def select(request):
        """
        Renders an overview of the probabilistic models with the option to
        select one to calculate an environmental contour.

        Parameters
        ----------
        request : HttpRequest,
            Request to select a probabilistic model to calculate a contour.

        Returns
        -------
        HttpResponse,
            Renders an overview of the probabilistic models with the option to
            select one to calculate an environmental contour.
        """
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
        Adds a ProbabilisticModel to the data base.

        Parameters
        ----------
        request : HttpRequest,
            Request to add the model to the data base.

        Returns
        -------
        HttpResponse,
            Renders feedback to the user based on whether she/he is:
            * logged in (normal behaviour)
            * Sent a defined probabilistic model as a POST request (normal
            behaviour)
            * Requested a form with a GET request or (unexpected beavhiour)

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
        Handles requests to calculate an environmental contour.

        This method handles both requests, for an IFORM contour and for a
        highest density contour.

        Parameters
        ----------
        request : HttpRequest,
            Request to calculate a contour.
        pk : int,
            Primary key of the probabilistic model, which the contour should be
            based on.
        method : str,
            Defines, which method should be used. Must be either 'I' form IFORM
            contour or 'H' for highest density contour.

        Returns
        -------
        HttpResponse,
            Renders the form for inputing all preprocessing options to calculate
            a contour.
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
        Sets the number of variables when a probabilistc model is defined
        directly.

        Parameters
        ----------
        request : HttpRequest,
            Request to set the number of variables of the probabilistic model.

        Returns
        -------
        HttpResponse,
            Either adds the probabilistic model to the data base (POST request)
            or renders the form to add a probabilistic model (GET request).
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
        Shows a probabilistic model.

        Parameters
        ----------
        request : HttpRequest,
            Request to show a probabilistic model.
        pk : int,
            Primary key of the probabilistic model.

        Returns
        -------
        HttpResponse,
            Renders the definition of the probabilistic model (its name,
            the probability density function, information about the fit)
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

            figure_collections = plot.sort_plotted_figures(probabilistic_model)

            return render(
                request,
                'contour/probabilistic_model_show.html',
                {'user': request.user,
                 'probabilistic_model': probabilistic_model,
                 'latex_string_list': latex_string_list,
                 'figure_collections': figure_collections})


class EnvironmentalContourHandler(Handler):
    """
    Handler for EnvironmentalContour objects.
    """

    @staticmethod
    def overview(request, model_class=models.EnvironmentalContour):
        return Handler.overview(request, model_class)

    @staticmethod
    def delete(request, pk, model_class=models.EnvironmentalContour):
        return Handler.delete(request, pk, model_class)

    @staticmethod
    def update(request, pk, model_class=models.EnvironmentalContour):
        return Handler.update(request, pk, model_class)

    @staticmethod
    def show(request, pk, model_class=models.EnvironmentalContour):
        return Handler.show(request, pk, model_class)

    @staticmethod
    def delete(request, pk, collection=models.EnvironmentalContour):
        return Handler.delete(request, pk, collection)


def save_fitted_prob_model(fit, model_title, var_names, var_symbols, user,
                           measure_file):
    """
    Saves a probabilistic model which was fitted to measurement data.

    Parameters
    ----------
    fit : Fit,
        Calculated fit results of a measurement file.
    model_title : str,
        Title of the probabilistic model.
    var_names : list of str,
        Names of the variables.
    var_symbols : list of str,
        Names of the symbols of the probabilistic model's variables.
    user : str,
        Name of a user.
    measure_file : MeasureFileModel,
        MeasureFileModel object linked to the probabilistic model.

    Returns
    -------
    ProbabilisticModel
        ProbabilisticModel that was fitted to the measurement file.

    """
    probabilistic_model = ProbabilisticModel(primary_user=user,
                                             collection_name=model_title,
                                             measure_file_model=measure_file)
    probabilistic_model.save()

    for i, dist in enumerate(fit.mul_var_dist.distributions):
        if dist.name == 'Lognormal':
            dist_name = 'Lognormal_SigmaMu'

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
            distribution_model = DistributionModel(
                name=var_names[i],
                symbol=var_symbols[i],
                probabilistic_model=probabilistic_model,
                distribution=dist.name
            )
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
    EnvironmentalContour,
        The saved environmental contour object.
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
    Reads the variable names and symbols form a csv file.
    
    Parameters
    ----------
    url : str,
        Path to the csv file.

    Returns
    -------
    var_names : list of str,
        Names of the environmental variables used in csv file,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']
    var_symbols : list of str,
        Symbols of the environental variables used in the csv file,
        e.g. ['V', 'Hs']
    """
    if url[0] == '/':
        url = url[1:]
    if url[0:8] == 'https://':
        req = request.Request(url)
        print('Trying to urlopen the url: ' + str(url))
        with request.urlopen(req) as response:
            reader = csv.reader(codecs.iterdecode(response, 'utf-8'), delimiter=';')
            var_names, var_symbols = get_header_info_from_reader(reader)
    else:
        with open(url, 'r') as file:
            reader = csv.reader(file, delimiter=';')
            var_names, var_symbols = get_header_info_from_reader(reader)

    return var_names, var_symbols


def get_header_info_from_reader(reader):
    """
    Reads the variable names and symbols form a reader.

    Parameters
    ----------
    reader : csv.Reader
        A Reader object that can read a file line by line.
        See https://docs.python.org/2/library/csv.html#reader-objects for
        a proper documentation.

    Returns
    -------
    var_names : list of str,
        Names of the environmental variables used in csv file,
        e.g. ['wind speed [m/s]', 'significant wave height [m]']
    var_symbols : list of str,
        Symbols of the environental variables used in the csv file,
        e.g. ['V', 'Hs']
    """
    var_names = []
    var_symbols = []
    for i, row in enumerate(reader):
        j = 0
        while j < (len(row)):
            # The first row contains the variable names.
            if i == 0:
                var_names.append(row[j])
            # The second row contains the variable symbols.
            elif i == 1:
                var_symbols.append(row[j])
            # The body starts at line 3, consequently we can stop here.
            elif i == 2:
                return var_names, var_symbols
            j += 1
    return var_names, var_symbols
