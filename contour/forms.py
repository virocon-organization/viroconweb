"""
Forms to handle user input.
"""
from django.forms import ModelForm
from django import forms
from .models import MeasureFileModel
from .validators import validate_csv_upload

# For subscript text
SUB = {ord(c): ord(t) for c, t in zip(u"0123456789", u"₀₁₂₃₄₅₆₇₈₉")}


class SecUserForm(ModelForm):
    class Meta:
        model = MeasureFileModel
        fields = ('secondary_user',)


class MeasureFileForm(forms.Form):
    """
    Form for uploading a measurement file.
    """
    title = forms.CharField(max_length=50, label='Title')
    measure_file = forms.FileField(label='Measurement file', max_length=255,
                                   validators=[validate_csv_upload])


class MeasureFileFitForm(forms.Form):
    """
    Form for defining a fit, which should be applied to a measurement file.
    """
    DISTRIBUTIONS = (('Weibull', 'Weibull'),('Normal', 'Normal'),
                     ('Lognormal_2', 'Log-Normal'))
    title = forms.CharField(max_length=50, label='Title')


    def __init__(self, variable_names, variable_count=2, *args, **kwargs):
        super(MeasureFileFitForm, self).__init__(*args, **kwargs)

        # First variable
        self.fields['_%s' % variable_names[0]] = forms.CharField(
            widget=forms.TextInput(
                attrs={'value': 'name',}
            ),
            max_length=50,
            label='1. Variable, ' + variable_names[0])
        self.fields['distribution_%s' % 0] = forms.ChoiceField(
            choices=self.DISTRIBUTIONS,
            initial='Weibull',
            label='Distribution',
            widget = forms.Select(attrs={
                'class': 'form-control'
            })
        )
        self.fields['width_of_intervals_%s' % 0] = forms.DecimalField(
            decimal_places=4,
            min_value=0.0001,
            widget=forms.NumberInput(attrs={'value': '2'}),
            label='Width of intervals')

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
                widget=forms.TextInput(attrs={
                    'value': 'name',}),
                label= str(i+1) + '. Variable, ' + variable_names[i])
            self.fields['distribution_%s' % i] = forms.ChoiceField(
                choices=self.DISTRIBUTIONS, initial='Weibull',
                label='Distribution',
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'id': 'dist_%s' % i,
                    'onclick': func_call})
                )
            if i < (variable_count-1):
                self.fields['width_of_intervals_%s' % i] = forms.DecimalField(
                    decimal_places=4,
                    min_value=0.0001,
                    widget=forms.NumberInput(attrs={'value': '2'}),
                    label='Width of intervals')

            self.fields['scale_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='α dependency',
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'id': 'scale_%s' % i
                })
            )
            self.fields['shape_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='β dependency',
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'id': 'shape_%s' % i
                })
            )
            self.fields['location_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='γ dependency',
                widget=forms.Select(attrs={
                    'class': 'form-control',
                    'id': 'loc_%s' % i})
            )


class VariablesForm(forms.Form):
    """
    Form for the direct input of a probabilistic model.
    """
    DISTRIBUTIONS = (('Normal', 'Normal'), ('Weibull', 'Weibull'),
                     ('Lognormal_2', 'Log-normal'))

    def __init__(self, variable_count=2, *args, **kwargs):
        super(VariablesForm, self).__init__(*args, **kwargs)

        self.variable_count = variable_count
        self.fields['variable_name_%s' % 0] = forms.CharField(
            min_length=3,
            label='1. Variable name',
            widget=forms.TextInput(
                attrs={'value': 'e.g. significant wave height [m]'}))
        self.fields['variable_symbol_%s' % 0] = forms.CharField(
            min_length=1,
            max_length=3,
            label='1. Variable symbol',
            widget=forms.TextInput(attrs={'value': 'e.g. Hs'}))
        i=0
        func_call = 'dist_select("dist_{}", "{}")'.format(i, i)
        self.fields['distribution_%s' % 0] = forms.ChoiceField(
            choices=self.DISTRIBUTIONS,
            initial='Weibull', label='Distribution',
            widget=forms.Select(attrs={'class': 'distribution form-control',
                                       'id': 'dist_0',
                                       'onclick': func_call}))
        self.fields['scale_%s' % 0 + '_%s' % 0] = forms.DecimalField(
            decimal_places=4,
            min_value=0.0001,
            label='α:'.translate(SUB),
            widget=forms.NumberInput(attrs={'value': '2.776',
                                            'id': 'scale_0_0'}))
        self.fields['shape_%s' % 0 + '_%s' % 0] = forms.DecimalField(
            decimal_places=4,
            min_value=0.0001,
            label='β:'.translate(SUB),
            widget=forms.NumberInput(attrs={'value': '1.471',
                                            'id': 'shape_0_0'}))
        self.fields['location_%s' % 0 + '_%s' % 0] = forms.DecimalField(
            decimal_places=4, min_value=0.0001,
            label='γ:'.translate(SUB),
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
                min_length=3, label=str(i + 1) + '. Variable name')
            self.fields['variable_symbol_%s' % i] = forms.CharField(
                max_length=3,
                label=str(i + 1) + '. Variable symbol',
                min_length=1)
            self.fields['distribution_%s' % i] = forms.ChoiceField(
                choices=self.DISTRIBUTIONS,
                initial='Weibull', label='Distribution',
                widget=forms.Select(attrs={'class': 'form-control',
                                           'id': 'dist_{}'.format(i),
                                           'onclick': func_call}))
            # Scale
            dependency_id = 'scale_{}'.format(i)
            param_class = 'scale_param%s' % i
            dist_id = 'dist_{}'.format(i)
            func_call = 'dependentChooser("' + dependency_id + '", "' + \
                        param_class + '", "' + dist_id + '")'.format(i)
            self.fields['scale_dependency_%s' % i] = forms.ChoiceField(
                choices=condition, required=False,
                label='α dependency',
                widget=forms.Select(attrs={'class': 'form-control',
                                           'id': dependency_id,
                                           'onclick': func_call}))
            for j in range(0, 3):
                if j == 0:
                    self.fields['scale_%s' % i + '_%s' % j] = \
                        forms.DecimalField(
                            decimal_places=4,
                            label='Constant value:',
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
                label='β dependency',
                widget=forms.Select(
                    attrs={'class': 'form-control',
                           'id': dependency_id,
                           'onclick': func_call}))
            for j in range(0, 3):
                if j == 0:
                    self.fields['shape_%s' % i + '_%s' % j] = \
                        forms.DecimalField(decimal_places=4,
                                           label='Constant value:',
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

            # Location
            dependency_id = 'location_{}'.format(i)
            param_class = 'location_param%s' % i
            dist_id = 'dist_{}'.format(i)
            func_call = 'dependentChooser("' + dependency_id + '", "' + \
                        param_class + '", "' + dist_id + '")'.format(i)
            self.fields['location_dependency_%s' % i] = forms.ChoiceField(
                choices=condition,
                required=False,
                label='γ dependency',
                widget=forms.Select(
                    attrs={'class': 'form-control',
                           'id': dependency_id,
                           'onclick': func_call}))
            for j in range(0, 3):
                if j == 0:
                    self.fields['location_%s' % i + '_%s' % j] = \
                        forms.DecimalField(
                            decimal_places=4,
                            required=False,
                            label='Constant value:',
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

    collection_name = forms.CharField(max_length=50, label='Title')



class VariableNumber(forms.Form):
    """
    Form for specifying the numbers of variables a probabilistic model should
    have.
    """
    variable_number = forms.IntegerField(
        min_value=2,
        max_value=10,
        label='Number of environmental variables')


class HDCForm(forms.Form):
    """
    Form for the settings to calculate a highest density contour (HDC).
    """
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
        label='Return period [years]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=10000,
        widget=forms.NumberInput(
            attrs={'value': '1.0',
                   'class': 'contour_input_field'}))
    sea_state = forms.DecimalField(
        label='Environmental state duration [hours]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=1000,
            widget=forms.NumberInput(
                attrs={'value': '3.0',
                       'class': 'contour_input_field'}))
    method = 'HDC'


class IFormForm(forms.Form):
    """
    Form for the input to calculate an IFORM contour.
    """
    return_period = forms.DecimalField(
        label='Return period [years]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=10000,
        widget=forms.NumberInput(
            attrs={'value': '1.0',
                   'class': 'contour_input_field'}))
    sea_state = forms.DecimalField(
        label='Environmental state duration [hours]',
        required=True,
        decimal_places=2,
        min_value=0.01,
        max_value=1000,
            widget=forms.NumberInput(
                attrs={'value': '3.0',
                       'class': 'contour_input_field'}))
    n_steps = forms.IntegerField(
        label='Number of points on the contour',
        required=True,
        min_value=5,
        max_value=10000,
        widget=forms.NumberInput(attrs={'value': '50',
                                     'class': 'contour_input_field'}))
    method = 'IFORM'
