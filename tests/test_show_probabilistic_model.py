from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class ShowProbModelTestCase(TestCase):

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

    def test_show_prob_model(self):
        response = self.client.post(reverse('enviro:probabilistic_model_show',
                                            kwargs={'pk': 1}),
                                    follow=True)
        # check if the H of H_s is formated by latexify
        self.assertContains(response, '<span class="django-latexify'
                                      ' math inline">f_{H_{s}}(h_{s})=',
                            status_code=200)
