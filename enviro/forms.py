from django.forms import ModelForm
from django import forms
from .models import MeasureFileModel

"""
shortens command for subscript text
"""
SUB = {ord(c): ord(t) for c, t in zip(u"0123456789", u"₀₁₂₃₄₅₆₇₈₉")}


class MeasureForm(ModelForm):
    class Meta:
        model = MeasureFileModel
        exclude = ('secondary_user', 'upload_date', 'primary_user')


class SecUserForm(ModelForm):
    class Meta:
        model = MeasureFileModel
        fields = ('secondary_user',)


class MeasureFileForm(forms.Form):
    title = forms.CharField(max_length=50, label='title')
    measure_file = forms.FileField(label='measurement file', max_length=255)


class MeasureFileFitForm(forms.Form):
    DISTRIBUTIONS = (('Weibull', 'Weibull'),('Normal', 'Normal'),
                     ('Lognormal_2', 'Log-Normal'))
    title = forms.CharField(max_length=50, label='title')


    def __init__(self, variable_names, variable_count=2, *args, **kwargs):
        super(MeasureFileFitForm, self).__init__(*args, **kwargs)

        # First variable
        self.fields['_%s' % variable_names[0]] = forms.CharField(
            widget=forms.TextInput(attrs={'value': 'name'}),
            max_length=50)
        self.fields['distribution_%s' % 0] = forms.ChoiceField(
            choices=self.DISTRIBUTIONS,
            widget=forms.Select,
            initial='Weibull',
            label='distribution')
        self.fields['width_of_intervals_%s' % 0] = forms.DecimalField(
            decimal_places=4,
            min_value=0.0001,
            widget=forms.NumberInput(attrs={'value': '2'}),
            label='width of intervals')

        # Additional variables
        for i in range(1, variable_count):
            condition = []
            condition.append(('!None', 'none'))
            for j in range(0, variable_count):
                if j < i:
                    condition.append((str(j) + 'f1', variable_names[j] +
                                      ' - power function'))
                    condition.append((str(j) + 'f2', variable_names[j] +
                                      ' - exponential'))

            func_call = 'dist_select("dist_{}", "{}")'.format(i, i)

            self.fields['_%s' % variable_names[i]] = forms.CharField(
                widget=forms.TextInput(attrs={'value': 'name'}))
            self.fields['distribution_%s' % i] = forms.ChoiceField(
                choices=self.DISTRIBUTIONS, initial='Weibull',
                widget=forms.Select(attrs={'id': 'dist_%s' % i,
                                          'onclick': func_call}),
                label='distribution')
            if i < (variable_count-1):
                self.fields['width_of_intervals_%s' % i] = forms.DecimalField(
                    decimal_places=4,
                    min_value=0.0001,
                    widget=forms.NumberInput(attrs={'value': '2'}),
                    label='width of intervals')

            self.fields['scale_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='scale (λ) dependency')
            self.fields['shape_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='shape (k) dependency',
                widget=forms.Select(attrs={'id': 'shape_%s' % i}))
            self.fields['location_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='location (θ) dependency',
                widget=forms.Select(attrs={'id': 'loc_%s' % i}))



class VariablesForm(forms.Form):
    DISTRIBUTIONS = (('Normal', 'Normal'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-Normal'))

    def __init__(self, variable_count=2, *args, **kwargs):
        super(VariablesForm, self).__init__(*args, **kwargs)

        self.fields['variable_name_%s' % 0] = forms.CharField(
            min_length=3,
            label='1. variable name',
            widget=forms.TextInput(
                attrs={'value': 'e.g. significant wave height [m]'}))
        self.fields['variable_symbol_%s' % 0] = forms.CharField(
            min_length=1,
            max_length=3,
            label='1. variable symbol',
            widget=forms.TextInput(attrs={'value': 'e.g. Hs'}))
        i=0
        func_call = 'dist_select("dist_{}", "{}")'.format(i, i)
        self.fields['distribution_%s' % 0] = forms.ChoiceField(
            choices=self.DISTRIBUTIONS,
            initial='Weibull', label='distribution',
            widget=forms.Select(attrs={'class': 'distribution',
                                       'id': 'dist_0',
                                       'onclick': func_call}))
        self.fields['scale_%s' % 0 + '_%s' % 0] = forms.DecimalField(
            decimal_places=4,
            min_value=0.0001,
            label='scale (λ):'.translate(SUB),
            widget=forms.NumberInput(attrs={'value': '2.776',
                                            'id': 'scale_0_0'}))
        self.fields['shape_%s' % 0 + '_%s' % 0] = forms.DecimalField(
            decimal_places=4,
            min_value=0.0001,
            label='shape (k):'.translate(SUB),
            widget=forms.NumberInput(attrs={'value': '1.471',
                                            'id': 'shape_0_0'}))
        self.fields['location_%s' % 0 + '_%s' % 0] = forms.DecimalField(
            decimal_places=4, min_value=0.0001,
            label='location (θ):'.translate(SUB),
            widget=forms.NumberInput(attrs={'value': '0.8888',
                                            'id': 'loc_0_0'}))

        for i in range(1, variable_count):
            condition = []
            condition.append(('!None', 'none'))
            for j in range(0, variable_count):
                if j < i:
                    condition.append((str(j) + 'f1', str(j + 1) +
                                      '. variable - power function'))
                    condition.append((str(j) + 'f2', str(j + 1) +
                                      '. variable - exponential'))
            func_call = 'dist_select("dist_{}", "{}")'.format(i, i)
            self.fields['variable_name_%s' % i] = forms.CharField(
                min_length=3, label=str(i + 1) + '. variable name')
            self.fields['variable_symbol_%s' % i] = forms.CharField(
                max_length=3,
                label=str(i + 1) + '. variable symbol',
                min_length=1)
            self.fields['distribution_%s' % i] = forms.ChoiceField(
                choices=self.DISTRIBUTIONS,
                initial='Weibull', label='distribution',
                widget=forms.Select(attrs={'id': 'dist_{}'.format(i),
                                           'onclick': func_call}))
            # Scale
            dependency_id = 'scale_{}'.format(i)
            param_class = 'scale_param%s' % i
            dist_id = 'dist_{}'.format(i)
            func_call = 'dependentChooser("' + dependency_id + '", "' + \
                        param_class + '", "' + dist_id + '")'.format(i)
            self.fields['scale_dependency_%s' % i] = forms.ChoiceField(
                choices=condition, required=False,
                label='scale (λ) dependency',
                widget=forms.Select(attrs={'id': dependency_id,
                                           'onclick': func_call}))
            for j in range(0, 3):
                if j == 0:
                    self.fields['scale_%s' % i + '_%s' % j] = \
                        forms.DecimalField(
                            decimal_places=4,
                            label='constant value:',
                            required=False,
                            initial=0,
                            widget=forms.NumberInput(
                                attrs={'class': param_class,
                                       'value': '1.489'}))
                else:
                    self.fields['scale_%s' % i + '_%s' % j] = \
                        forms.DecimalField(decimal_places=4,
                                           label='',
                                           required=False,
                                           initial=0,
                                           widget=forms.NumberInput(
                                               attrs={'class': param_class,
                                                      'style': 'display:none',
                                                      'value': '1.489'}))

            # Shape
            dependency_id = 'shape_{}'.format(i)
            param_class = 'shape_param%s' % i
            dist_id = 'dist_{}'.format(i)
            func_call = 'dependentChooser("' + dependency_id + '", "' + \
                        param_class + '", "' + dist_id + '")'.format(i)
            self.fields['shape_dependency_%s' % i] = forms.ChoiceField(
                choices=condition, required=False,
                label='shape (k) dependency',
                widget=forms.Select(
                    attrs={'id': dependency_id,
                           'onclick': func_call}))
            for j in range(0, 3):
                if j == 0:
                    self.fields['shape_%s' % i + '_%s' % j] = \
                        forms.DecimalField(decimal_places=4,
                                           label='constant value:',
                                           required=False,
                                           initial=0,
                                           widget=forms.NumberInput(
                                               attrs={'class': param_class,
                                                      'value': '1.489'}))
                else:
                    self.fields['shape_%s' % i + '_%s' % j] = \
                        forms.DecimalField(decimal_places=4,
                                           label='',
                                           required=False,
                                           initial=0,
                                           widget=forms.NumberInput(
                                               attrs={
                                                   'class': param_class,
                                                   'style': 'display:none',
                                                   'value': '1.489'}))

            # location
            dependency_id = 'location_{}'.format(i)
            param_class = 'location_param%s' % i
            dist_id = 'dist_{}'.format(i)
            func_call = 'dependentChooser("' + dependency_id + '", "' + \
                        param_class + '", "' + dist_id + '")'.format(i)
            self.fields['location_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='location (θ) dependency',
                widget=forms.Select(
                    attrs={'id': dependency_id,
                           'onclick': func_call}))
            for j in range(0, 3):
                if j == 0:
                    self.fields['location_%s' % i + '_%s' % j] = \
                        forms.DecimalField(
                            decimal_places=4,
                            required=False,
                            label='constant value:',
                            widget=forms.NumberInput(
                                attrs={'class': param_class,
                                       'value': '0'}))
                else:
                    self.fields['location_%s' % i + '_%s' % j] = \
                        forms.DecimalField(decimal_places=4,
                                           required=False,
                                           label='',
                                           widget=forms.NumberInput(
                                               attrs={
                                                   'class': param_class,
                                                   'style': 'display:none',
                                                   'value': '0'}))

    collection_name = forms.CharField(max_length=50, label='title')



class VariableNumber(forms.Form):
    variable_number = forms.IntegerField(
        min_value=2,
        max_value=10,
        label='number of environmental variables')


class HDCForm(forms.Form):
    def __init__(self, var_names, *args, **kwargs):
        super(HDCForm, self).__init__(*args, **kwargs)
        for i, name in enumerate(var_names):
            self.fields['limit_%s' % i + '_1'] = forms.DecimalField(
                label=name + ' lower limit',
                required=True,
                decimal_places=4,
                min_value=0,
                max_value=10000,
                widget=forms.NumberInput(
                    attrs={'value': '0',
                           'class': 'contour_input_field'}))
            self.fields['limit_%s' % i + '_2'] = forms.DecimalField(
                label=name + ' upper limit',
                required=True,
                decimal_places=4,
                min_value=0.01,
                max_value=10000,
                widget=forms.NumberInput(
                    attrs={'value': '20',
                           'class': 'contour_input_field'}))
            self.fields['delta_%s' % i] = forms.DecimalField(
                label=name + ' grid size ',
                 required=True,
                 decimal_places=4,
                 min_value=0.01,
                 max_value=1000,
                 widget=forms.NumberInput(
                     attrs={'value': '0.5',
                            'class': 'contour_input_field'}))
        pass

    n_years = forms.DecimalField(
        label='return period [years]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=10000,
        widget=forms.NumberInput(
            attrs={'value': '1.0',
                   'class': 'contour_input_field'}))
    sea_state = forms.DecimalField(
        label='environmental state duration [hours]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=1000,
            widget=forms.NumberInput(
                attrs={'value': '3.0',
                       'class': 'contour_input_field'}))
    method = 'HDC'


class IFormForm(forms.Form):
    return_period = forms.DecimalField(
        label='return period [years]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=10000,
        widget=forms.NumberInput(
            attrs={'value': '1.0',
                   'class': 'contour_input_field'}))
    sea_state = forms.DecimalField(
        label='environmental state duration [hours]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=1000,
            widget=forms.NumberInput(
                attrs={'value': '3.0',
                       'class': 'contour_input_field'}))
    n_steps = forms.IntegerField(
        label='number of points on the contour',
        required=True,
        min_value=5,
        max_value=10000,
        widget=forms.NumberInput(attrs={'value': '50',
                                     'class': 'contour_input_field'}))
    method = 'IFORM'
