from django.test import TestCase, Client, override_settings
from django.core.urlresolvers import reverse
from contour.forms import HDCForm


class EnvironmentalContourTestCase(TestCase):

    def setUp(self):
        # Login
        self.client = Client()
        self.client.post(reverse('user:authentication'),
                         {'username': 'max_mustermann',
                          'password': 'Musterpasswort2018'})

        # Create a form containing the information of a 2D probabilistic model
        form_input_dict = {
            'variable_name_0': 'significant wave height [m]',
            'variable_symbol_0': 'Hs',
            'distribution_0': 'Weibull',
            'scale_0_0': '2.776',
            'shape_0_0': '1.471',
            'location_0_0': '0.888',
            'variable_name_1': 'peak period [s]',
            'variable_symbol_1': 'Tp',
            'distribution_1': 'Lognormal_SigmaMu',
            'scale_dependency_1': '0power3',
            'scale_1_0': '0.1',
            'scale_1_1': '1.489',
            'scale_1_2': '0.1901',
            'shape_dependency_1': '0exp3',
            'shape_1_0': '0.04',
            'shape_1_1': '0.1748',
            'shape_1_2': '-0.2243',
            'location_dependency_1': '!None',
            'location_1_0': '0',
            'location_1_1': '0',
            'location_1_2': '0',
            'collection_name': 'direct input Vanem2012'
        }

        # Create a 2D probabilistic model
        self.client.post(reverse('contour:probabilistic_model_add',
                                 args=['02']),
                         form_input_dict,
                         follow=True)

        # Create a form containing the information of a 4D probabilistic model
        form_input_dict = {
            'variable_name_0': 'significant wave height [m]',
            'variable_symbol_0': 'Hs',
            'distribution_0': 'Weibull',
            'scale_0_0': '2.776',
            'shape_0_0': '1.471',
            'location_0_0': '0.888',
            'variable_name_1': 'peak period [s]',
            'variable_symbol_1': 'Tp',
            'distribution_1': 'Lognormal_SigmaMu',
            'scale_dependency_1': '0power3',
            'scale_1_0': '0.1',
            'scale_1_1': '1.489',
            'scale_1_2': '0.1901',
            'shape_dependency_1': '0exp3',
            'shape_1_0': '0.04',
            'shape_1_1': '0.1748',
            'shape_1_2': '-0.2243',
            'location_dependency_1': '!None',
            'location_1_0': '0',
            'location_1_1': '0',
            'location_1_2': '0',
            'variable_name_2': 'wind speed [m/s]',
            'variable_symbol_2': 'V',
            'distribution_2': 'Weibull',
            'scale_dependency_2': '!None',
            'scale_2_0': '2',
            'scale_2_1': '0',
            'scale_2_2': '0',
            'shape_dependency_2': '!None',
            'shape_2_0': '1',
            'shape_2_1': '0',
            'shape_2_2': '0',
            'location_dependency_2': '!None',
            'location_2_0': '1',
            'location_2_1': '0',
            'location_2_2': '0',
            'variable_name_3': 'wind speed [m/s]',
            'variable_symbol_3': 'V',
            'distribution_3': 'Weibull',
            'scale_dependency_3': '!None',
            'scale_3_0': '2',
            'scale_3_1': '0',
            'scale_3_2': '0',
            'shape_dependency_3': '!None',
            'shape_3_0': '1',
            'shape_3_1': '0',
            'shape_3_2': '0',
            'location_dependency_3': '!None',
            'location_3_0': '1',
            'location_3_1': '0',
            'location_3_2': '0',
            'collection_name': 'Generic 4D model'
        }

        # Create a 4D probabilistic model
        self.client.post(reverse('contour:probabilistic_model_add',
                                 args=['04']),
                         form_input_dict,
                         follow=True)

    # Since this test is affected by whitenoise, we deactive it here, see:
    # https://stackoverflow.com/questions/30638300/django-test-redirection-fail
    @override_settings(STATICFILES_STORAGE=None)
    def test_2d_iform_contour(self):
        response = self.client.get(reverse('contour:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'I'}),
                                    follow=True)
        # check if html of the IFORM input view is correct
        self.assertContains(response, 'umber of points on the contour',
                            status_code=200)

        # check if html of the IFORM results view is correct
        form_input_dict = {
            'return_period' : '1',
            'sea_state' : '3',
            'n_steps' : '50',
            'method' : 'IFORM'
        }
        response = self.client.post(reverse('contour:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'I'}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, 'Download report',
                            status_code=200)

        # Finally delete the environmental contour. This servers two purposes:
        # 1. To test it
        # 2. To avoid amassing .png and .pdf files each time the test is run
        response = self.client.get(reverse('contour:environmental_contour_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)

    # Since this test is affected by whitenoise, we deactive it here, see:
    # https://stackoverflow.com/questions/30638300/django-test-redirection-fail
    @override_settings(STATICFILES_STORAGE=None)
    def test_4d_iform_contour(self):
        response = self.client.get(reverse('contour:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'I'}),
                                    follow=True)
        # check if html of the IFORM input view is correct
        self.assertContains(response, 'umber of points on the contour',
                            status_code=200)

        # check if html of the IFORM results view is correct
        form_input_dict = {
            'return_period' : '1',
            'sea_state' : '3',
            'n_steps' : '50',
            'method' : 'IFORM'
        }
        response = self.client.post(reverse('contour:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'I'}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, 'Download report',
                            status_code=200)

        # Finally delete the environmental contour. This servers two purposes:
        # 1. To test it
        # 2. To avoid amassing .png and .pdf files each time the test is run
        response = self.client.get(reverse('contour:environmental_contour_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)

    # Since this test is affected by whitenoise, we deactive it here, see:
    # https://stackoverflow.com/questions/30638300/django-test-redirection-fail
    @override_settings(STATICFILES_STORAGE=None)
    def test_2d_highest_density_contour(self):
        response = self.client.get(reverse('contour:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'H'}),
                                    follow=True)
        # check if html of the HDC input view is correct
        self.assertContains(response, 'grid size',
                            status_code=200)

        # create a HDC input form
        form_input_dict = {
            'limit_0_1' : '0',
            'limit_0_2' : '20',
            'delta_0' : '0.5',
            'limit_1_1' : '0',
            'limit_1_2' : '20',
            'delta_1' : '0.5',
            'n_years' : '1',
            'sea_state' : '3',
            'method' : 'HDC'
        }
        form = HDCForm(data=form_input_dict,
                         var_names=['significant wave height [m]',
                                    'peak period [s]'])
        self.assertTrue(form.is_valid())

        # check if html of the HDC results view is correct
        response = self.client.post(reverse('contour:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'H'}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, 'Download report',
                            status_code=200)

        # Finally delete the environmental contour. This servers two purposes:
        # 1. To test it
        # 2. To avoid amassing .png and .pdf files each time the test is run
        response = self.client.get(reverse('contour:environmental_contour_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)
