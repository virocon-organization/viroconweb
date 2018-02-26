from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from enviro.forms import HDCForm


class EnvironmentalContourTestCase(TestCase):

    def setUp(self):
        # create a user
        self.client = Client()
        self.client.post(reverse('user:create'),
                         {'username': 'max_mustermann',
                          'email': 'max.mustermann@gmail.com',
                          'first_name': 'Max',
                          'last_name': 'Mustermann',
                          'organisation': 'Musterfirma',
                          'type_of_use': 'commercial',
                          'password1': 'Musterpasswort2018',
                          'password2': 'Musterpasswort2018'})

        # create a form containing the information of the  probabilistic model
        form_input_dict = {
            'variable_name_0': 'significant wave height [m]',
            'variable_symbol_0': 'Hs',
            'distribution_0': 'Weibull',
            'scale_0_0': '2.776',
            'shape_0_0': '1.471',
            'location_0_0': '0.888',
            'variable_name_1': 'peak period [s]',
            'variable_symbol_1': 'Tp',
            'distribution_1': 'Lognormal_2',
            'scale_dependency_1': '0f1',
            'scale_1_0': '0.1',
            'scale_1_1': '1.489',
            'scale_1_2': '0.1901',
            'shape_dependency_1': '0f2',
            'shape_1_0': '0.04',
            'shape_1_1': '0.1748',
            'shape_1_2': '-0.2243',
            'location_dependency_1': '!None',
            'location_1_0': '0',
            'location_1_1': '0',
            'location_1_2': '0',
            'collection_name': 'direct input Vanem2012'
        }

        # create a probabilistic model
        self.client.post(reverse('enviro:probabilistic_model_add',
                                 args=['02']),
                         form_input_dict,
                         follow=True)


    def test_iform_contour(self):
        response = self.client.get(reverse('enviro:probabilistic_model_calc',
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
        response = self.client.post(reverse('enviro:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'I'}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, 'Download PDF',
                            status_code=200)

    def test_highest_density_contour(self):
        response = self.client.get(reverse('enviro:probabilistic_model_calc',
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
        response = self.client.post(reverse('enviro:probabilistic_model_calc',
                                            kwargs={'pk' : '1',
                                                    'method': 'H'}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, 'Download PDF',
                            status_code=200)
