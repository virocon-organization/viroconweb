from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from enviro.forms import MeasureFileForm


class UploadFileTestCase(TestCase):

    def setUp(self):

        self.test_files_path = os.path.abspath(os.path.join(os.path.dirname( __file__), r'test_files/'))
        self.client = Client()
        self.client.post(reverse('user:create'),
                           {'username' : 'max_mustermann',
                            'email' : 'max.mustermann@gmail.com',
                            'first_name' : 'Max',
                            'last_name' : 'Mustermann',
                            'organisation' : 'Musterfirma',
                            'type_of_use' : 'commercial',
                            'password1' : 'Musterpasswort2018',
                            'password2' : 'Musterpasswort2018'})
        self.client.post(reverse('user:create'),
                           {'username' : 'sabine_mustermann',
                            'email' : 'sabine.mustermann@gmail.com',
                            'first_name' : 'Sabine',
                            'last_name' : 'Mustermann',
                            'organisation' : 'Musterfirma',
                            'type_of_use' : 'academic',
                            'password1' : 'Musterpasswort2018',
                            'password2' : 'Musterpasswort2018'})

    def test_upload_file(self):

        file_name = '1yeardata_vanem2012pdf_withHeader.csv'

        # Thanks to: https://stackoverflow.com/questions/2473392/unit-testing-
        # a-django-form-with-a-filefield
        test_file = open(os.path.join(self.test_files_path , file_name), 'rb')
        test_file_simple_uploaded = SimpleUploadedFile(test_file.name,
                                                       test_file.read())
        post_dict = {'title' : 'Test Title'}
        file_dict = {'measure_file' : test_file_simple_uploaded}

        # First test the form.
        form = MeasureFileForm(post_dict, file_dict)
        self.assertTrue(form.is_valid())

        # Then test the view, which contains a plot of the file.
        response = self.client.post(reverse('enviro:measure_file_model_add'),
                                    {'title' : file_name,
                                     'measure_file' : test_file_simple_uploaded
                                    },
                                    follow=True)
        self.assertContains(response, "scatter plot", status_code = 200)

        # Then share the file with another user. First show the view.
        response = self.client.get(reverse('enviro:measure_file_model_update',
                                           kwargs={'pk': 1}),
                                    follow=True)
        self.assertContains(response, "secondary user",
                            status_code = 200)
        # Then post that the file should be shared with a secondary user.
        # Use a non-existing user name, one should be redirected to home and an
        # error message should be shown.
        response = self.client.post(reverse('enviro:measure_file_model_update',
                                           kwargs={'pk': 1}),
                                    {'username': 'non_existing_user'},
                                    follow=True)
        self.assertContains(response, "Apply methods",
                            status_code = 200)
        # Use an existing user name, one should be redirected to the overview.
        response = self.client.post(reverse('enviro:measure_file_model_update',
                                           kwargs={'pk': 1}),
                                    {'username': 'sabine_mustermann'},
                                    follow=True)
        self.assertContains(response, "Uploaded measurement files",
                            status_code = 200)

        # Finally delete the uploaded file. This servers two purposes:
        # 1. To test it
        # 2. To avoid adding up .csv files in the dir each time the test is run
        response = self.client.get(reverse('enviro:measure_file_model_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)
        self.assertContains(response, "Uploaded measurement files",
                            status_code = 200)
