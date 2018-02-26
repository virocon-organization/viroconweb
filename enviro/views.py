import os
import csv
import warnings

from abc import abstractmethod
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404, HttpResponse, \
    HttpResponseRedirect
from django.core.exceptions import ValidationError
from django.contrib import messages

from . import forms
from . import plot
from . import settings

from .models import User, MeasureFileModel
from .compute_interface import ComputeInterface


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
            return HttpResponseRedirect('/home')
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

            base = 'enviro:' + collection.url_str()
            html = 'enviro/' + collection.url_str() + '_overview.html'
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
            return HttpResponseRedirect('/home')
        else:
            instance = get_object_or_404(collection, pk=pk)

            if instance.primary_user == request.user:
                instance.delete()
            else:
                instance.secondary_user.remove(request.user)
            redirection = 'enviro:' + collection.url_str() + '_overview'
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
            return HttpResponseRedirect('/home')
        else:
            redirection = 'enviro:' + collection.url_str() + '_overview'
            template = 'enviro/update_sec_user.html'
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
                        return redirect('home:home')
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
       :return:            different HttpResponses. Success: redirect to a certain model overview, Fault: return info
                           about wrong input.
       """

    @staticmethod
    @abstractmethod
    def select(request):
        """
        The method returns a HttpResponse where you can select a File from a Model to do further calculations. 
        :return:        HttpResponse to select an item form a certain model. 
        """


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
            return HttpResponseRedirect('/home')
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

            return render(request, 'enviro/measure_file_model_select.html', {'context': context})

    @staticmethod
    def add(request):
        """
        The method adds an item to MeasureFile 
        :return: 
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            measure_file_form = forms.MeasureFileForm()
            if request.method == 'POST':
                measure_file_form = forms.MeasureFileForm(data=request.POST, files=request.FILES)
                if measure_file_form.is_valid():
                    measure_model = MeasureFileModel(primary_user=request.user,
                                                     title=measure_file_form.cleaned_data['title'],
                                                     measure_file=measure_file_form.cleaned_data['measure_file'])
                    measure_model.save()
                    return redirect('enviro:measure_file_model_plot', measure_model.pk)
                else:
                    return render(request, 'enviro/measure_file_model_add.html', {'form': measure_file_form})
            else:
                return render(request, 'enviro/measure_file_model_add.html', {'form': measure_file_form})

    @staticmethod
    def fit_file(request, pk):
        """
        The method fits a MeasureFile item and shows the result. If the fit isn't possible the user is going to be
        informed with an error message.
        :return:        HttpResponse.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            mfm_item = MeasureFileModel.objects.get(pk=pk)
            var_names, var_symbols = get_info_from_file(mfm_item.measure_file.url[1:])
            var_number = len(var_names)
            fit_form = forms.MeasureFileFitForm(variable_count=var_number, variable_names=var_names)
            if request.method == 'POST':
                fit_form = forms.MeasureFileFitForm(data=request.POST, variable_count=var_number, variable_names=var_names)
                if fit_form.is_valid():
                    ci = ComputeInterface()
                    try:
                        fit = ci.fit_curves(mfm_item=mfm_item, fit_settings=fit_form.cleaned_data,
                                            var_number=var_number)
                    except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                        return render(request, 'enviro/error.html',
                                      {'error_message': err,
                                       'text': 'Error occured while fitting a probabliistic model to the file.'
                                               'Try it again with different settings please',
                                       'header': 'fit measurement file to probabilistic model',
                                       'return_url': 'enviro:measure_file_model_select'})
                    #try:
                    directory_prefix = settings.PATH_STATIC
                    directory_after_static = settings.PATH_USER_GENERATED + \
                                             str(request.user) + '/prob_model/'
                    directory = directory_prefix + directory_after_static
                    probabilistic_model = plot.plot_fits(fit, var_names, var_symbols, fit_form.cleaned_data['title'],
                                                         request.user, mfm_item, directory)
                    #except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                        #return render(request, 'enviro/error.html',
                        #              {'error_message': err,
                        #               'text': 'Error occured while plotting the fit.'
                        #                       'Try it again with different settings please',
                        #               'header': 'fit measurement file to probabilistic model',
                        #               'return_url': 'enviro:measure_file_model_select'})
                    multivariate_distribution = plot.setup_mul_dist(probabilistic_model)
                    latex_string_list = multivariate_distribution.latex_repr(var_symbols)
                    img_list = os.listdir(directory + '/' +  str(probabilistic_model.pk))
                    send_img = []
                    for img in img_list:
                        send_img.append(directory_after_static + str(probabilistic_model.pk) + '/' + img)
                    return render(request, 'enviro/fit_results.html', {'pk': probabilistic_model.pk, 'imgs': send_img,
                                                                       'latex_string_list': latex_string_list})
                else:
                    return render(request, 'enviro/measure_file_model_fit.html', {'form': fit_form})
            return render(request, 'enviro/measure_file_model_fit.html', {'form': fit_form})

    @staticmethod
    def new_fit(request, pk):
        """
        The method deletes the previous fit and returns the form to enter a new fit.
        :param request: to make a new fit.
        :param pk:      primary key of the previous fit. 
        :return:        HttpResponse to enter a new fit.     
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            plot.ProbabilisticModel.objects.all().filter(pk=pk).delete()
            user_files = MeasureFileModel.objects.all().filter(primary_user=request.user)
            return render(request, 'enviro/measure_file_model_select.html', {'context': user_files})

    @staticmethod
    def plot_file(request, pk):
        """
        The method plots a MeasureFile
        :return:        HttpResponse.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            measure_file_model = MeasureFileModel.objects.get(pk=pk)
            var_names, var_symbols = get_info_from_file(measure_file_model.measure_file.url[1:])
            directory_prefix = settings.PATH_STATIC
            directory_after_static = settings.PATH_USER_GENERATED + \
                                     str(request.user) + \
                                     '/measurement/' + str(pk)
            directory = directory_prefix + directory_after_static
            plot.plot_data_set_as_scatter(request.user, measure_file_model, var_names, directory)
            return render(request, 'enviro/measure_file_model_plot.html', {'user': request.user,
                                                                     'measure_file_model':measure_file_model,
                                                                     'directory': directory_after_static})


class ProbabilisticModelHandler(Handler):
    @staticmethod
    def overview(request, collection=plot.ProbabilisticModel):
        return Handler.overview(request, collection)

    @staticmethod
    def delete(request, pk, collection=plot.ProbabilisticModel):
        return Handler.delete(request, pk, collection)

    @staticmethod
    def update(request, pk, collection=plot.ProbabilisticModel):
        return Handler.update(request, pk, collection)

    @staticmethod
    def select(request):
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            user_pm = plot.ProbabilisticModel.objects.all().filter(primary_user=request.user)
            return render(request, 'enviro/probabilistic_model_select.html', {'context': user_pm})

    @staticmethod
    def add(request, *args):
        """
        The method adds an item to the ProbabilisticModel (database).
        :param request:     to add an item to the model. 
        :param var_num:     number of variables which should be added to the model. 
        :return:            different HttpResponses. Success: redirect to select probabilistic model, Fault: return info
                            about wrong input.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            var_num = args[0]
            var_num_int = int(var_num)
            variable_form = forms.VariablesForm(variable_count=var_num_int)
            var_num_form = forms.VariableNumber()
            if request.method == 'POST':
                variable_form = forms.VariablesForm(data=request.POST, variable_count=var_num_int)
                if variable_form.is_valid():
                    is_valid_probabilistic_model = True
                    probabilistic_model = plot.ProbabilisticModel(primary_user=request.user,
                                                                  collection_name=variable_form.cleaned_data[
                                                                 'collection_name'], measure_file_model=None)
                    probabilistic_model.save()
                    for i in range(var_num_int):
                        distribution = plot.DistributionModel(name=variable_form.cleaned_data['variable_name_' + str(i)],
                                                              distribution=variable_form.cleaned_data[
                                                             'distribution_' + str(i)],
                                                              symbol=variable_form.cleaned_data['variable_symbol_' + str(i)],
                                                              probabilistic_model=probabilistic_model)
                        distribution.save()
                        params = ['shape', 'location', 'scale']
                        if i == 0:
                            for param in params:
                                parameter = plot.ParameterModel(function='None',
                                                                x0=variable_form.cleaned_data[param + '_' + str(i) + '_0'],
                                                                dependency='!',
                                                                name=param, distribution=distribution)
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
                                parameter = plot.ParameterModel(
                                    function=variable_form.cleaned_data[param + '_dependency_' + str(i)][1:],
                                    x0=variable_form.cleaned_data[param + '_' + str(i) + '_0'],
                                    x1=variable_form.cleaned_data[param + '_' + str(i) + '_1'],
                                    x2=variable_form.cleaned_data[param + '_' + str(i) + '_2'],
                                    dependency=variable_form.cleaned_data[param + '_dependency_' + str(i)][0],
                                    name=param, distribution=distribution)
                                try:
                                    parameter.clean()
                                except ValidationError as e:
                                    messages.add_message(request,
                                                         messages.ERROR,
                                                         e.message)
                                    is_valid_probabilistic_model = False
                                else:
                                    parameter.save()
                    if is_valid_probabilistic_model:
                        return redirect('enviro:probabilistic_model_select')
                    else:
                        probabilistic_model.delete()
                        return render(request,
                                      'enviro/probabilistic_model_add.html',
                                      {'form': variable_form,
                                       'var_num_form': var_num_form})
                else:
                    return render(request,
                                  'enviro/probabilistic_model_add.html',
                                  {'form': variable_form,
                                   'var_num_form': var_num_form})

            return render(request, 'enviro/probabilistic_model_add.html',
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
            return HttpResponseRedirect('/home')
        else:
            item = plot.ProbabilisticModel.objects.get(pk=pk)
            var_names = []
            var_symbols = []
            dists_model = plot.DistributionModel.objects.filter(probabilistic_model=item)

            for dist in dists_model:
                var_names.append(dist.name)
                var_symbols.append(dist.symbol)
            if method == 'I':
                return ProbabilisticModelHandler.iform_calc(request, var_names, var_symbols, item)
            elif method == 'H':
                return ProbabilisticModelHandler.hdc_calc(request, var_names, var_symbols, item)
            else:
                KeyError('{} no matching calculation method')

    @staticmethod
    def iform_calc(request, var_names, var_symbols, probabilistic_model):
        """
        The method gives the ifrom calculation order.
        :param request:             user request to use the iform calculation method. 
        :param var_names:           names of the variables.
        :param var_symbols:         symbols of the variables of the probabilistic model.
        :param probabilistic_model: which is used to create a contour. 
        :return:                    HttpResponse with the generated graphic (pdf) or error message.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            iform_form = forms.IFormForm()
            cs = ComputeInterface
            if request.method == 'POST':
                iform_form = forms.IFormForm(data=request.POST)
                if iform_form.is_valid():
                    try:
                        contour_coordinates = cs.iform(
                            probabilistic_model,
                            float(iform_form.cleaned_data['return_period']),
                            float(iform_form.cleaned_data['sea_state']),
                            iform_form.cleaned_data['n_steps'])
                        method = Method(
                            "", "IFORM",
                            float(iform_form.cleaned_data['return_period']),
                            float(iform_form.cleaned_data['sea_state']),
                            {"Number of points on the contour":
                                 iform_form.cleaned_data['n_steps']})
                    # catch and allocate errors caused by calculating iform.
                    except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                        return render(request, 'enviro/error.html', {'error_message': err,
                                                                     'text': 'Try it again with other settings please',
                                                                     'header': 'calculate Contour',
                                                                     'return_url': 'enviro:probabilistic_model_select'})

                    path = plot.create_latex_report(contour_coordinates, str(request.user), ''.join(['T = ',
                                                                                                str(iform_form.cleaned_data['return_period']),
                                   ' years, method = IFORM']), probabilistic_model, var_names, var_symbols, method)


                    #probabilistic_model.measure_file_model.measure_file
                    # if matrix 4dim - send data for 4dim interactive plot.
                    if len(contour_coordinates[0]) == 4:
                        dists = plot.DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
                        labels = []
                        for dist in dists:
                            labels.append('{} [{}]'.format(dist.name, dist.symbol))
                        return render(request, 'enviro/contour_result.html',
                                      {'path': path, 'x': contour_coordinates[0][0].tolist(), 'y': contour_coordinates[0][1].tolist(),
                                       'z': contour_coordinates[0][2].tolist(), 'u': contour_coordinates[0][3].tolist(), 'dim': 4,
                                       'labels': labels})
                    # if matrix 3dim - send data for 3dim interactive plot
                    elif len(contour_coordinates[0]) == 3:
                        dists = plot.DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
                        labels = []
                        for dist in dists:
                            labels.append('{} [{}]'.format(dist.name, dist.symbol))
                        return render(request, 'enviro/contour_result.html',
                                      {'path': path, 'x': contour_coordinates[0][0].tolist(), 'y': contour_coordinates[0][1].tolist(),
                                       'z': contour_coordinates[0][2].tolist(), 'dim': 3, 'labels': labels})

                    elif len(contour_coordinates) < 3:
                        return render(request, 'enviro/contour_result.html', {'path': path, 'dim': 2})
                else:
                    return render(request, 'enviro/contour_settings.html', {'form': iform_form})
            else:
                return render(request, 'enviro/contour_settings.html', {'form': iform_form})

    @staticmethod
    def hdc_calc(request, var_names, var_symbols, probabilistic_model):
        """
        The method gives the hdc calculation order. If the calculation does not work the user gets an error messages.
        :param request:             user request to use the hdc calculation method. 
        :param var_names:           names of the variables.
        :param var_symbols:         symbols of the variables of the probabilistic model
        :param probabilistic_model: which is used to create a contour. 
        :return:                    HttpResponse with the generated graphic (pdf) or error message.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            hdc_form = forms.HDCForm(var_names=var_names)
            cs = ComputeInterface()
            if request.method == 'POST':
                hdc_form = forms.HDCForm(data=request.POST, var_names=var_names)
                if hdc_form.is_valid():
                    limits = []
                    deltas = []
                    warn = None
                    contour_matrix = None
                    for i in range(len(var_names)):
                        limits.append(
                            (float(hdc_form.cleaned_data['limit_%s' % i + '_1']),
                             float(hdc_form.cleaned_data['limit_%s' % i + '_2'])))
                        deltas.append(float(hdc_form.cleaned_data['delta_%s' % i]))
                    try:
                        with warnings.catch_warnings(record=True) as warn:
                            contour_matrix = cs.hdc(
                                probabilistic_model,
                                float(hdc_form.cleaned_data['n_years']),
                                float(hdc_form.cleaned_data['sea_state']),
                                limits, deltas)
                            method = Method("", "Highest Density Contour (HDC)", float(hdc_form.cleaned_data['n_years']),
                                            hdc_form.cleaned_data['sea_state'], {"Limits of the grid":limits, r"""Grid cell size ($\Delta x_i$)""":deltas})
                    # catch and allocate errors caused by calculating hdc.
                    except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                        return render(request, 'enviro/error.html', {'error_message': err,
                                                                     'text': 'Try it again with other settings please',
                                                                     'header': 'calculate Contour',
                                                                     'return_url': 'enviro:probabilistic_model_select'})

                    # generate path to the user specific pdf.
                    path = plot.create_latex_report(contour_matrix, str(request.user), ''.join(['T = ',
                                                                                                str(hdc_form.cleaned_data['n_years']),
                                    ' years, method = HDC']),
                                                    probabilistic_model, var_names, var_symbols, method)

                    # if matrix 3dim - send data for 3dim interactive plot.
                    if len(contour_matrix[0]) > 2:
                        dists = plot.DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
                        labels = []
                        for dist in dists:
                            labels.append('{} [{}]'.format(dist.name, dist.symbol))
                        return render(request, 'enviro/contour_result.html',
                                      {'path': path, 'x': contour_matrix[0][0].tolist(), 'y': contour_matrix[0][1].tolist(),
                                       'z': contour_matrix[0][2].tolist(), 'dim': 3, 'warn': warn, 'labels': labels})
                    else:
                        return render(request, 'enviro/contour_result.html', {'path': path, 'dim': 2, 'warn': warn})
                else:
                    return render(request, 'enviro/contour_settings.html', {'form': hdc_form})
            else:
                return render(request, 'enviro/contour_settings.html', {'form': hdc_form})

    @staticmethod
    def set_variables_number(request):
        """
        The method sets the variable number in the VariablesForm
        :param request:     user request to change the variable number 
        :return:            a VariablesForm with the certain variable number 
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            var_num_str = str()
            if request.method == 'POST':
                var_num_form = forms.VariableNumber(request.POST)
                if var_num_form.is_valid():
                    var_num = var_num_form.cleaned_data['variable_number']
                    var_num_str = str(var_num)
                    if int(var_num) < 10:
                        var_num_str = '0' + var_num_str
                return redirect('enviro:probabilistic_model_add', var_num_str)
            else:
                variable_form = forms.VariablesForm()
                var_num_form = forms.VariableNumber()
                return render(request, 'enviro/probabilistic_model_add.html',
                              {'form': variable_form, 'var_num_form': var_num_form})

    @staticmethod
    def show_model(request, pk):
        """
        The method shows a probabilistic model (name, equation of the joint pdf, information about the fit)
        :return:        HttpResponse.
        """
        if request.user.is_anonymous:
            return HttpResponseRedirect('/home')
        else:
            probabilistic_model = plot.ProbabilisticModel.objects.get(pk=pk)
            dists_model = plot.DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
            var_symbols = []
            for dist in dists_model:
                var_symbols.append(dist.symbol)
            multivariate_distribution = plot.setup_mul_dist(probabilistic_model)
            latex_string_list = multivariate_distribution.latex_repr(var_symbols)
            send_img = []

            directory_prefix = settings.PATH_STATIC
            directory_after_static = settings.PATH_USER_GENERATED + str(request.user) + \
                                     '/prob_model/' + str(pk)
            directory = directory_prefix + directory_after_static
            if os.path.isdir(directory):
                img_list = os.listdir(directory)
                for img in img_list:
                    send_img.append(directory_after_static + '/' + img)
            directory_measure_plot_after_prefix = ''
            if probabilistic_model.measure_file_model:
                directory_measure_plot_after_prefix = \
                    settings.PATH_USER_GENERATED +str(request.user) + \
                    '/measurement/' + \
                    str(probabilistic_model.measure_file_model.pk) + \
                    '/scatter.png'

            return render(request, 'enviro/probabilistic_model_show.html',
                          {'user': request.user, 'probabilistic_model': probabilistic_model,
                           'latex_string_list': latex_string_list, 'imgs': send_img,
                          'directory_measure_plot_after_prefix': directory_measure_plot_after_prefix})


def download_pdf(request):
    """
    The function returns a pdf download with the results of the contour calculation.
    :param request:     user request to download a certain result pdf.
    :return:            result pdf 
    """
    if request.user.is_anonymous:
        return HttpResponseRedirect('/home')
    else:
        response = HttpResponse(content_type='application/pdf')
        path = 'attachment; filename="' + settings.PATH_STATIC + \
               settings.PATH_USER_GENERATED + str(request.user) + \
               '/contour/latex_report.pdf"'
        response['Content-Disposition'] = path
        return response


def get_info_from_file(url):
    """
    The function reads the variable names form a csv. file.
    :param url:     path of the csv. file.
    :return:        the names of the variables.
    """
    with open(url, 'r') as file:
        reader = csv.reader(file, delimiter=';').__next__()
        var_names = []
        var_symbols = []
        i = 0
        while i < (len(reader)):
            var_names.append(reader[i])
            i += 1
            var_symbols.append(reader[i])
            i += 1
        return var_names, var_symbols


class Method:
    def __init__(self, fitting_method, contour_method, return_period, state_duration, additional_options=None):
        self.fitting_method = fitting_method
        self.contour_method = contour_method
        self.return_period = return_period
        self.state_duration = state_duration
        self.additional_options = additional_options
