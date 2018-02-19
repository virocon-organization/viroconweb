from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from enviro.forms import MeasureFileFitForm


class FitProbModelTestCase(TestCase):

    def setUp(self):
        # Create a user
        self.client = Client()
        self.client.post(reverse('user:create'),
                           {'username' : 'max_mustermann',
                            'email': 'max.mustermann@gmail.com',
                            'first_name': 'Max',
                            'last_name': 'Mustermann',
                            'organisation': 'Musterfirma',
                            'type_of_use': 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2': 'Musterpasswort2018'})

    def test_fit_probabilistic_model_vanem2012(self):
        # Create a measurement file
        test_files_path = os.path.abspath(os.path.join(os.path.dirname( __file__), r'test_files/'))
        file_name = '1yeardata_vanem2012pdf_withHeader.csv'

        # Thanks to: https://stackoverflow.com/questions/2473392/unit-testing-
        # a-django-form-with-a-filefield
        test_file = open(os.path.join(test_files_path , file_name), 'rb')
        test_file_simple_uploaded = SimpleUploadedFile(test_file.name,
                                                       test_file.read())
        self.client.post(reverse('enviro:measure_file_model_add'),
                                    {'title' : file_name,
                                     'measure_file' : test_file_simple_uploaded
                                    })

        # Open fitting url and check if the html is correct
        response = self.client.get(reverse('enviro:measure_file_model_fit',
                                            kwargs={'pk' : 1}))
        self.assertContains(response, "example_normal.svg", status_code=200)

        # Create a fitting form without input
        form = MeasureFileFitForm(
            variable_count=2,
            variable_names=['significant wave height [m]', 'peak period [s]'])

        # Create a fitting form with input (Vanem2012 model, like the test data)
        form_input_dict = {
                'title' : 'Test fit',
                '_significant wave height [m]' : 'significant wave height [m]',
                'distribution_0' : 'Weibull',
                'width_of_intervals_0' : '2',
                '_peak period [s]': 'peak period [s]',
                'distribution_1' : 'Lognormal_2',
                'scale_dependency_1' : '0f2',
                'shape_dependency_1' : '0f1',
                'location_dependency_1' : '!None'
            }
        form = MeasureFileFitForm(
            data=form_input_dict,
            variable_names=['significant wave height [m]', 'peak period [s]'],
            variable_count=2)
        self.assertTrue(form.is_valid())

        # Test if the fit worked and the correct view is shown
        response = self.client.post(reverse('enviro:measure_file_model_fit',
                                            kwargs={'pk' : 1}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, "Visual inspection", status_code=200)

        # Finally delete the uploaded file. This servers two purposes:
        # 1. To test it
        # 2. To avoid adding up .csv files in the dir each time the test is run
        response = self.client.get(reverse('enviro:measure_file_model_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)
        self.assertContains(response, "ploaded measurement files",
                            status_code = 200)

    def test_fit_probabilistic_model_no_dependency(self):
        # Create a measurement file
        test_files_path = os.path.abspath(os.path.join(os.path.dirname( __file__), r'test_files/'))
        file_name = '1yeardata_vanem2012pdf_withHeader.csv'

        # Thanks to: https://stackoverflow.com/questions/2473392/unit-testing-
        # a-django-form-with-a-filefield
        test_file = open(os.path.join(test_files_path , file_name), 'rb')
        test_file_simple_uploaded = SimpleUploadedFile(test_file.name,
                                                       test_file.read())
        self.client.post(reverse('enviro:measure_file_model_add'),
                                    {'title' : file_name,
                                     'measure_file' : test_file_simple_uploaded
                                    })
        # --- WEIBULL-WEIBULL ---
        # Create a fitting form with the input of a Weibull-Weibull model,
        # which has no no depedencies
        form_input_dict = {
                'title' : 'Weibull Weibull, interval width: 2',
                '_significant wave height [m]' : 'significant wave height [m]',
                'distribution_0' : 'Weibull',
                'width_of_intervals_0' : '2',
                '_peak period [s]': 'peak period [s]',
                'distribution_1' : 'Weibull',
                'scale_dependency_1' : '!None',
                'shape_dependency_1' : '!None',
                'location_dependency_1' : '!None'
            }
        form = MeasureFileFitForm(
            data=form_input_dict,
            variable_names=['significant wave height [m]', 'peak period [s]'],
            variable_count=2)
        self.assertTrue(form.is_valid())

        # Test if the fit worked and the correct view is shown.
        response = self.client.post(reverse('enviro:measure_file_model_fit',
                                            kwargs={'pk' : 1}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, "Visual inspection", status_code=200)

        # --- WEIBULL-NORMAL ---
        # Create a fitting form with the input of a Weibull-Normal model,
        # which has no no depedencies
        form_input_dict = {
                'title' : 'Weibull Normal, interval width: 2',
                '_significant wave height [m]' : 'significant wave height [m]',
                'distribution_0' : 'Weibull',
                'width_of_intervals_0' : '2',
                '_peak period [s]': 'peak period [s]',
                'distribution_1' : 'Normal',
                'scale_dependency_1' : '!None',
                'shape_dependency_1' : '!None',
                'location_dependency_1' : '!None'
            }
        form = MeasureFileFitForm(
            data=form_input_dict,
            variable_names=['significant wave height [m]', 'peak period [s]'],
            variable_count=2)
        self.assertTrue(form.is_valid())

        # Test if the fit worked and the correct view is shown
        response = self.client.post(reverse('enviro:measure_file_model_fit',
                                            kwargs={'pk' : 1}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, "Visual inspection", status_code=200)

        # Finally delete the uploaded file. This servers two purposes:
        # 1. To test it
        # 2. To avoid adding up .csv files in the dir each time the test is run
        response = self.client.get(reverse('enviro:measure_file_model_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)
        self.assertContains(response, "ploaded measurement files",
                            status_code = 200)
