from django.forms import ModelForm
from django import forms
from .models import MeasureFileManager
from django.utils import timezone
from django.forms.extras.widgets import SelectDateWidget
from decimal import Decimal

"""
shortens command for subscript text
"""
SUB = {ord(c): ord(t) for c, t in zip(u"0123456789", u"₀₁₂₃₄₅₆₇₈₉")}


class MeasureForm(ModelForm):
    class Meta:
        model = MeasureFileManager
        exclude = ('secondary_user', 'upload_date', 'primary_user')


class SecUserForm(ModelForm):
    class Meta:
        model = MeasureFileManager
        fields = ('secondary_user',)


class MeasureFileForm(forms.Form):
    title = forms.CharField(max_length=20, label='title')
    measure_file = forms.FileField(label='measurement file',max_length=255)


class MeasureFileFitForm(forms.Form):
    DISTRIBUTIONS = (('Weibull', 'Weibull'),('Normal', 'Normal'),
                     ('Lognormal_2', 'Log-Normal'))

    def __init__(self, variable_names, variable_count=2, *args, **kwargs):
        super(MeasureFileFitForm, self).__init__(*args, **kwargs)

        self.fields['_%s' % variable_names[0]] = forms.CharField(widget=forms.TextInput(attrs={'value': 'name'}))
        self.fields['distribution_%s' % 0] = forms.ChoiceField(choices=self.DISTRIBUTIONS, widget=forms.Select,
                                                               initial='Weibull', label='distribution')

        for i in range(1, variable_count):
            condition = []
            condition.append(('!None', 'none'))
            for j in range(0, variable_count):
                if j < i:
                    condition.append((str(j) + 'f1', variable_names[j] + ' - polynomial'))
                    condition.append((str(j) + 'f2', variable_names[j] + ' - exponential'))

            func_call = 'dist_select("dist_{}", "{}")'.format(i, i)

            self.fields['_%s' % variable_names[i]] = forms.CharField(widget=forms.TextInput(attrs={'value': 'name'}))
            self.fields['distribution_%s' % i] = forms.ChoiceField(choices=self.DISTRIBUTIONS, initial='Weibull',
                                                                   widget=forms.Select(attrs={'id': 'dist_%s' % i,
                                                                                              'onclick': func_call}),
                                                                   label='distribution')
            self.fields['scale_dependency_%s' % i] = forms.ChoiceField(choices=condition, required=False,
                                                                       label='scale dependency')
            self.fields['shape_dependency_%s' % i] = forms.ChoiceField(choices=condition, required=False,
                                                                       label='shape dependency',
                                                                       widget=forms.Select(
                                                                           attrs={'id': 'shape_%s' % i}))
            self.fields['location_dependency_%s' % i] = forms.ChoiceField(choices=condition, required=False,
                                                                          label='location dependency',
                                                                          widget=forms.Select(
                                                                              attrs={'id': 'loc_%s' % i}))

    title = forms.CharField(max_length=25, label='title')
    number_of_intervals = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '15'}), label='number of intervals')


class VariablesForm(forms.Form):
    DISTRIBUTIONS = (('Normal', 'Normal'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-Normal'))

    def __init__(self, variable_count=2, *args, **kwargs):
        super(VariablesForm, self).__init__(*args, **kwargs)

        self.fields['variable_name_%s' % 0] = forms.CharField(min_length=3, label='1. variable name')
        self.fields['variable_symbol_%s' % 0] = forms.CharField(max_length=3, label='1. variable symbol', min_length=1)
        self.fields['distribution_%s' % 0] = forms.ChoiceField(choices=self.DISTRIBUTIONS,
                                                               initial='Weibull', label='distribution',
                                                               widget=forms.Select(
                                                                   attrs={'class': 'distribution',
                                                                          'id': 'dist_0'}))
        self.fields['scale_%s' % 0 + '_%s' % 0] = forms.DecimalField(decimal_places=4, min_value=0.0001,
                                                                     label='scale'.translate(SUB),
                                                                     widget=forms.NumberInput(
                                                                         attrs={'value': '2.776',
                                                                                'id': 'scale_0_0'}))
        self.fields['shape_%s' % 0 + '_%s' % 0] = forms.DecimalField(decimal_places=4, min_value=0.0001,
                                                                     label='shape'.translate(SUB),
                                                                     widget=forms.NumberInput(
                                                                         attrs={'value': '1.471',
                                                                                'id': 'shape_0_0'}))
        self.fields['location_%s' % 0 + '_%s' % 0] = forms.DecimalField(decimal_places=4, min_value=0.0001,
                                                                        label='location'.translate(SUB),
                                                                        widget=forms.NumberInput(
                                                                            attrs={'value': '0.8888',
                                                                                   'id': 'loc_0_0'}))

        for i in range(1, variable_count):
            condition = []
            condition.append(('!None', 'none'))
            for j in range(0, variable_count):
                if j < i:
                    condition.append((str(j) + 'f1', str(j + 1) + '. variable - polynomial'))
                    condition.append((str(j) + 'f2', str(j + 1) + '. variable - exponential'))
            func_call = 'dist_select("dist_{}", "{}")'.format(i, i)
            self.fields['variable_name_%s' % i] = forms.CharField(min_length=3, label=str(i + 1) + '. variable name')
            self.fields['variable_symbol_%s' % i] = forms.CharField(max_length=3,
                                                                    label=str(i + 1) + '. variable symbol',
                                                                    min_length=1)
            self.fields['distribution_%s' % i] = forms.ChoiceField(choices=self.DISTRIBUTIONS,
                                                                   initial='Weibull', label='distribution',
                                                                   widget=forms.Select(
                                                                       attrs={
                                                                           'id': 'dist_{}'.format(i),
                                                                           'onclick': func_call}))
            # scale
            dependency_id = 'scale_{}'.format(i)
            params_class = 'scale_param%s' % i
            func_call = 'dependentChooser("' + dependency_id + '", "' + params_class + '")'
            self.fields['scale_dependency_%s' % i] = forms.ChoiceField(choices=condition, required=False,
                                                                       label='scale dependency',
                                                                       widget=forms.Select(
                                                                           attrs={'id': dependency_id,
                                                                                  'onclick': func_call,
                                                                                  }))
            for j in range(0, 3):
                if j == 0:
                    self.fields['scale_%s' % i + '_%s' % j] = forms.DecimalField(decimal_places=4,
                                                                                 label='c%s' % str(j).translate(SUB),
                                                                                 required=False, initial=0,
                                                                                 widget=forms.NumberInput(
                                                                                     attrs={
                                                                                         'class': params_class,
                                                                                         'value': '1.489'}))
                else:
                    self.fields['scale_%s' % i + '_%s' % j] = forms.DecimalField(decimal_places=4,
                                                                                 label='c%s' % str(j).translate(SUB),
                                                                                 required=False, initial=0,
                                                                                 widget=forms.NumberInput(
                                                                                     attrs={
                                                                                         'class': params_class,
                                                                                         'style': 'display:none',
                                                                                         'value': '1.489'}))

            # shape
            dependency_id = 'shape_{}'.format(i)
            params_class = 'shape_param%s' % i
            func_call = 'dependentChooser("' + dependency_id + '", "' + params_class + '")'
            self.fields['shape_dependency_%s' % i] = forms.ChoiceField(choices=condition, required=False,
                                                                       label='shape dependency',
                                                                       widget=forms.Select(
                                                                           attrs={'id': dependency_id,
                                                                                  'onclick': func_call,
                                                                                  }))
            for j in range(0, 3):
                if j == 0:
                    self.fields['shape_%s' % i + '_%s' % j] = forms.DecimalField(decimal_places=4,
                                                                                 label="c%s" % str(j).translate(SUB),
                                                                                 required=False, initial=0,
                                                                                 widget=forms.NumberInput(
                                                                                     attrs={
                                                                                         'class': params_class,
                                                                                         'value': '1.489'}))
                else:
                    self.fields['shape_%s' % i + '_%s' % j] = forms.DecimalField(decimal_places=4,
                                                                                 label="c%s" % str(j).translate(SUB),
                                                                                 required=False, initial=0,
                                                                                 widget=forms.NumberInput(
                                                                                     attrs={
                                                                                         'class': params_class,
                                                                                         'style': 'display:none',
                                                                                         'value': '1.489'}))

            # location
            dependency_id = 'location_{}'.format(i)
            params_class = 'location_param%s' % i
            func_call = 'dependentChooser("' + dependency_id + '", "' + params_class + '")'
            self.fields['location_dependency_%s' % i] = forms.ChoiceField(choices=condition, required=False,
                                                                          label='location dependency',
                                                                          widget=forms.Select(
                                                                              attrs={'id': dependency_id,
                                                                                     'onclick': func_call,
                                                                                     }))
            for j in range(0, 3):
                if j == 0:
                    self.fields['location_%s' % i + '_%s' % j] = forms.DecimalField(decimal_places=4, required=False,
                                                                                    label='c%s' % str(j).translate(SUB),
                                                                                    widget=forms.NumberInput(
                                                                                        attrs={
                                                                                            'class': params_class,
                                                                                            'style': 'display:none',
                                                                                            'value': '0'}))
                else:
                    self.fields['location_%s' % i + '_%s' % j] = forms.DecimalField(decimal_places=4, required=False,
                                                                                    label='c%s' % str(j).translate(SUB),
                                                                                    widget=forms.NumberInput(
                                                                                        attrs={
                                                                                            'class': params_class,
                                                                                            'style': 'display:none',
                                                                                            'value': '0'}))

    collection_name = forms.CharField(max_length=25, label='title')



class VariableNumber(forms.Form):
    variable_number = forms.IntegerField(min_value=2, max_value=10, label='number of environmental variables')


class HDCForm(forms.Form):
    def __init__(self, var_names, *args, **kwargs):
        super(HDCForm, self).__init__(*args, **kwargs)
        for i, name in enumerate(var_names):
            self.fields['limit_%s' % i + '_1'] = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '0'}),
                                                                    label=name + ' lower limit')
            self.fields['limit_%s' % i + '_2'] = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '20'}),
                                                                    label=name + ' upper limit')
            self.fields['delta_%s' % i] = forms.DecimalField(widget=forms.NumberInput(attrs={'value': '0.5'}),
                                                             label=name + ' grid size ')
        pass

    n_years = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '25'}), label='return period [years]')

    sea_state = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '3'}),
                                   label='environmental state duration [hours]')
    method = 'HDC'


class IFormForm(forms.Form):
    return_period = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '25'}),
                                       label='return period [years]')
    sea_state = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '3'}),
                                   label='environmental state duration [hours]')
    n_steps = forms.IntegerField(widget=forms.NumberInput(attrs={'value': '50'}),
                                 label='number of points on the contour')
    method = 'IFORM'
