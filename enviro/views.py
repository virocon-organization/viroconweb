from abc import abstractmethod
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404, HttpResponse
from .forms import *
from .models import MeasureFileModel
from .compute.ComputeInterface import ComputeInterface
from .plot import *
import os
import csv
import warnings
import numpy as np
from scipy.optimize import OptimizeWarning


class Handler:
    @staticmethod
    def overview(request, collection):
        """
        The method overview shows a overview of all items in a specific database.
        :param request:     to load an overview of database model.
        :param collection:  the selected database.       
        :return:            HttpResponse. 
        """
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

        base = 'enviro:' + str(collection())
        html = 'enviro/' + str(collection()) + '_overview.html'
        update = base + '-update'
        delete = base + '-delete'
        add = base + '-add'
        calc = base + '-calc'

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
        instance = get_object_or_404(collection, pk=pk)

        if instance.primary_user == request.user:
            instance.delete()
        else:
            instance.secondary_user.remove(request.user)
        redirection = 'enviro:' + str(collection()) + '-overview'
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
        redirection = 'enviro:' + str(collection()) + '-overview'
        template = 'enviro/update_secUser.html'
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
                except:  # TODO What kind of Exception is excepted ?
                    return redirect('/home/')
                else:
                    instance.save()
            return redirect(redirection)
        else:
            return render(request, template, {'form': SecUserForm})

    @staticmethod
    @abstractmethod
    def add(request, **kwargs):
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

        return render(request, 'enviro/measurefiles_select.html', {'context': context})

    @staticmethod
    def add(request):
        """
        The method adds an item to MeasureFile 
        :return: 
        """
        measure_file_form = MeasureFileForm()
        if request.method == 'POST':
            measure_file_form = MeasureFileForm(data=request.POST, files=request.FILES)
            if measure_file_form.is_valid():
                measure_model = MeasureFileModel(primary_user=request.user,
                                                 title=measure_file_form.cleaned_data['title'],
                                                 measure_file=measure_file_form.cleaned_data['measure_file'])
                measure_model.save()
                return redirect('enviro:measurefiles-plot', measure_model.pk)
            else:
                print('invalid')
                return render(request, 'enviro/measurefiles_add.html', {'form': measure_file_form})
        else:
            return render(request, 'enviro/measurefiles_add.html', {'form': measure_file_form})

    @staticmethod
    def fit_file(request, pk):
        """
        The method fits a MeasureFile item and shows the result. If the fit isn't possible the user is going to be
        informed with an error message.
        :return:        HttpResponse.
        """
        mfm_item = MeasureFileModel.objects.get(pk=pk)
        var_names, var_symbols = get_info_from_file(mfm_item.measure_file.url[1:])
        var_number = len(var_names)
        fit_form = MeasureFileFitForm(variable_count=var_number, variable_names=var_names)
        if request.method == 'POST':
            fit_form = MeasureFileFitForm(data=request.POST, variable_count=var_number, variable_names=var_names)
            if fit_form.is_valid():
                ci = ComputeInterface()
                try:
                        fit = ci.fit_curves(mfm_item=mfm_item, fit_settings=fit_form.cleaned_data,
                                            var_number=var_number)
                except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                    return render(request, 'enviro/error.html',
                                  {'error_message': err,
                                   'text': 'Try it again with different settings please',
                                   'header': 'fit measurement file to probabilistic model',
                                   'return_url': 'enviro:measurefiles-select'})

                var_man_pk = plot_fits(fit, var_names, var_symbols, fit_form.cleaned_data['title'], request.user, mfm_item)
                img_list = os.listdir('enviro/static/' + str(request.user))
                send_img = []
                for img in img_list:
                    send_img.append(str(request.user) + '/' + img)
                    print(img)
                return render(request, 'enviro/fit_results.html', {'imgs': send_img, 'pk': var_man_pk})
            else:
                return render(request, 'enviro/measurefiles_fit.html', {'form': fit_form})
        return render(request, 'enviro/measurefiles_fit.html', {'form': fit_form})

    @staticmethod
    def new_fit(request, pk):
        """
        The method deletes the previous fit and returns the form to enter a new fit.
        :param request: to make a new fit.
        :param pk:      primary key of the previous fit. 
        :return:        HttpResponse to enter a new fit.     
        """
        ProbabilisticModel.objects.all().filter(pk=pk).delete()
        user_files = MeasureFileModel.objects.all().filter(primary_user=request.user)
        return render(request, 'enviro/measurefiles_select.html', {'context': user_files})

    @staticmethod
    def plot_file(request, pk):
        """
        The method plots a MeasureFile
        :return:        HttpResponse.
        """
        measure_file_model = MeasureFileModel.objects.get(pk=pk)
        var_names, var_symbols = get_info_from_file(measure_file_model.measure_file.url[1:])
        plot_data_set_as_scatter(request.user, measure_file_model, var_names)
        return render(request, 'enviro/measurefiles_plot.html', {'user': request.user, 'measure_file_model':measure_file_model})


class ProbabilisticModelHandler(Handler):
    @staticmethod
    def overview(request, collection=ProbabilisticModel):
        return Handler.overview(request, collection)

    @staticmethod
    def delete(request, pk, collection=ProbabilisticModel):
        return Handler.delete(request, pk, collection)

    @staticmethod
    def update(request, pk, collection=ProbabilisticModel):
        return Handler.update(request, pk, collection)

    @staticmethod
    def select(request):
        user_pm = ProbabilisticModel.objects.all().filter(primary_user=request.user)
        return render(request, 'enviro/probabilistic_model_select.html', {'context': user_pm})

    @staticmethod
    def add(request, var_num):
        """
        The method adds an item to the ProbabilisticModel (database).
        :param request:     to add an item to the model. 
        :param var_num:     number of variables which should be added to the model. 
        :return:            different HttpResponses. Success: redirect to select probabilistic model, Fault: return info
                            about wrong input.
        """
        var_num_int = int(var_num)
        variable_form = VariablesForm(variable_count=var_num_int)
        var_num_form = VariableNumber()
        if request.method == 'POST':
            variable_form = VariablesForm(data=request.POST, variable_count=var_num_int)
            if variable_form.is_valid():
                probabilistic_model = ProbabilisticModel(primary_user=request.user,
                                                         collection_name=variable_form.cleaned_data[
                                                             'collection_name'], measure_file_model=None)
                probabilistic_model.save()
                for i in range(var_num_int):
                    distribution = DistributionModel(name=variable_form.cleaned_data['variable_name_' + str(i)],
                                                     distribution=variable_form.cleaned_data[
                                                         'distribution_' + str(i)],
                                                     symbol=variable_form.cleaned_data['variable_symbol_' + str(i)],
                                                     probabilistic_model=probabilistic_model)
                    distribution.save()
                    params = ['shape', 'location', 'scale']
                    if i == 0:
                        for param in params:
                            parameter = ParameterModel(function='None',
                                                       x0=variable_form.cleaned_data[param + '_' + str(i) + '_0'],
                                                       dependency='!',
                                                       name=param, distribution=distribution)
                            parameter.save()

                    else:
                        for param in params:
                            parameter = ParameterModel(
                                function=variable_form.cleaned_data[param + '_dependency_' + str(i)][1:],
                                x0=variable_form.cleaned_data[param + '_' + str(i) + '_0'],
                                x1=variable_form.cleaned_data[param + '_' + str(i) + '_1'],
                                x2=variable_form.cleaned_data[param + '_' + str(i) + '_2'],
                                dependency=variable_form.cleaned_data[param + '_dependency_' + str(i)][0],
                                name=param, distribution=distribution)

                            parameter.save()

                return redirect('enviro:probabilistic_model-select')
            else:
                return render(request, 'enviro/probabilistic_model_add.html',
                              {'form': variable_form, 'var_num_form': var_num_form})

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
        item = ProbabilisticModel.objects.get(pk=pk)
        print(item)
        var_names = []
        var_symbols = []
        dists_model = DistributionModel.objects.filter(probabilistic_model=item)

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
        iform_form = IFormForm()
        cs = ComputeInterface
        if request.method == 'POST':
            iform_form = IFormForm(data=request.POST)
            if iform_form.is_valid():
                try:
                    contour_matrix = cs.iform(probabilistic_model, iform_form.cleaned_data['return_period'],
                                              iform_form.cleaned_data['sea_state'], iform_form.cleaned_data['n_steps'])
                    method = Method("", "IFORM", float(iform_form.cleaned_data['return_period']))
                # catch and allocate errors caused by calculating iform.
                except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                    return render(request, 'enviro/error.html', {'error_message': err,
                                                                 'text': 'Try it again with other settings please',
                                                                 'header': 'calculate Contour',
                                                                 'return_url': 'enviro:probabilistic_model-select'})

                path = plot_pdf(contour_matrix, str(request.user), ''.join(['T = ',
                                str(iform_form.cleaned_data['return_period']),
                                ' years, IFORM']), probabilistic_model, var_names, var_symbols, method)

                #probabilistic_model.measure_file_model.measure_file
                # if matrix 4dim - send data for 4dim interactive plot.
                if len(contour_matrix[0]) == 4:
                    dists = DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
                    labels = []
                    for dist in dists:
                        labels.append('{} [{}]'.format(dist.name, dist.symbol))
                    return render(request, 'enviro/contour_result.html',
                                  {'path': path, 'x': contour_matrix[0][0].tolist(), 'y': contour_matrix[0][1].tolist(),
                                   'z': contour_matrix[0][2].tolist(), 'u': contour_matrix[0][3].tolist(), 'dim': 4,
                                   'labels': labels})
                # if matrix 3dim - send data for 3dim interactive plot
                elif len(contour_matrix[0]) == 3:
                    dists = DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
                    labels = []
                    for dist in dists:
                        labels.append('{} [{}]'.format(dist.name, dist.symbol))
                    return render(request, 'enviro/contour_result.html',
                                  {'path': path, 'x': contour_matrix[0][0].tolist(), 'y': contour_matrix[0][1].tolist(),
                                   'z': contour_matrix[0][2].tolist(), 'dim': 3, 'labels': labels})

                elif len(contour_matrix) < 3:
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
        hdc_form = HDCForm(var_names=var_names)
        cs = ComputeInterface()
        if request.method == 'POST':
            hdc_form = HDCForm(data=request.POST, var_names=var_names)
            if hdc_form.is_valid():
                limits = []
                deltas = []
                warn = None
                contour_matrix = None
                for i in range(len(var_names)):
                    limits.append(
                        (int(hdc_form.cleaned_data['limit_%s' % i + '_1']),
                         int(hdc_form.cleaned_data['limit_%s' % i + '_2'])))
                    deltas.append(float(hdc_form.cleaned_data['delta_%s' % i]))
                try:
                    with warnings.catch_warnings(record=True) as warn:
                        contour_matrix = cs.hdc(probabilistic_model, hdc_form.cleaned_data['n_years'],
                                                hdc_form.cleaned_data['sea_state'], limits, deltas)
                        method = Method("", "Highest Density Contour (HDC)", float(hdc_form.cleaned_data['n_years']))
                # catch and allocate errors caused by calculating hdc.
                except (ValueError, RuntimeError, IndexError, TypeError, NameError, KeyError, Exception) as err:
                    return render(request, 'enviro/error.html', {'error_message': err,
                                                                 'text': 'Try it again with other settings please',
                                                                 'header': 'calculate Contour',
                                                                 'return_url': 'enviro:probabilistic_model-select'})

                # generate path to the user specific pdf.
                path = plot_pdf(contour_matrix, str(request.user),  ''.join(['T = ',
                                str(hdc_form.cleaned_data['n_years']),
                                ' years, Highest Density Contour (HDC)']),
                                probabilistic_model, var_names, var_symbols, method)

                # if matrix 3dim - send data for 3dim interactive plot.
                if len(contour_matrix[0]) > 2:
                    dists = DistributionModel.objects.filter(probabilistic_model=probabilistic_model)
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
        var_num_str = str()
        if request.method == 'POST':
            var_num_form = VariableNumber(request.POST)
            if var_num_form.is_valid():
                var_num = var_num_form.cleaned_data['variable_number']
                var_num_str = str(var_num)
                if int(var_num) < 10:
                    var_num_str = '0' + var_num_str
            return redirect('enviro:probabilistic_model-add', var_num_str)
        else:
            variable_form = VariablesForm()
            var_num_form = VariableNumber()
            return render(request, 'enviro/probabilistic_model_add.html',
                          {'form': variable_form, 'var_num_form': var_num_form})


def download_pdf(request):
    """
    The function returns a pdf download with the results of the contour calculation.
    :param request:     user request to download a certain result pdf.
    :return:            result pdf 
    """
    response = HttpResponse(content_type='application/pdf')
    path = 'attachment; filename="enviro/static/' + str(request.user) + '/contour_table.pdf"'
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
    def __init__(self, fitting_method, contour_method, return_period):
        self.fitting_method = fitting_method
        self.contour_method = contour_method
        self.return_period = return_period

