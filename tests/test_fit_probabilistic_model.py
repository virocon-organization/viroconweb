from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from enviro.forms import MeasureFileFitForm


class FitProbModelTestCase(TestCase):
    def setUp(self):
        # create a user
        self.client = Client()
        self.client.post(reverse('user:create'),
                           {'username' : 'max_mustermann',
                            'email': 'max.mustermann@gmail.com',
                            'first_name': 'Max',
                            'last_name': 'Mustermann',
                            'organisation': 'Musterfirma',
                            'type_of_use': 'commercial',
                            'password1' : 'AnJaKaTo2018',
                            'password2': 'AnJaKaTo2018'})

        # create a measurement file
        test_files_path = os.path.abspath(os.path.join(os.path.dirname( __file__), r'test_files/'))
        file_name = '1yeardata_vanem2012pdf_withHeader.csv'

        # thanks to: https://stackoverflow.com/questions/2473392/unit-testing-
        # a-django-form-with-a-filefield
        test_file = open(os.path.join(test_files_path , file_name), 'rb')
        test_file_simple_uploaded = SimpleUploadedFile(test_file.name,
                                                       test_file.read())
        self.client.post(reverse('enviro:measurefiles-add'),
                                    {'title' : file_name,
                                     'measure_file' : test_file_simple_uploaded
                                    })


    def test_fit_probabilistic_model(self):
        # open fitting url and check if the html is correct
        response = self.client.post(reverse('enviro:measurefiles-fit',
                                            kwargs={'pk' : 1}))
        self.assertContains(response, "example_normal.svg", status_code=200)

        # create a fitting form without input
        form = MeasureFileFitForm(
            variable_count=2,
            variable_names=['significant wave height [m]', 'peak period [s]'])

        # create a fitting form with input (Vanem2012 model, like the test data)
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

        # test if the fit worked and the correct view is shown
        response = self.client.post(reverse('enviro:measurefiles-fit',
                                            kwargs={'pk' : 1}),
                                    form_input_dict,
                                    follow=True)
        self.assertContains(response, "Visual inspection", status_code=200)