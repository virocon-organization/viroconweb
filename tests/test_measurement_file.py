from django.test import TestCase, Client, override_settings
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from contour.forms import MeasureFileForm


class UploadFileTestCase(TestCase):

    def setUp(self):

        self.test_files_path = os.path.abspath(os.path.join(os.path.dirname( __file__), r'test_files/'))
        self.client = Client()
        # Login
        self.client.post(reverse('user:authentication'),
                           {'username' : 'max_mustermann',
                            'password' : 'Musterpasswort2018'})

    # Since this test is affected by whitenoise, we deactive it here, see:
    # https://stackoverflow.com/questions/30638300/django-test-redirection-fail
    @override_settings(STATICFILES_STORAGE=None)
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
        response = self.client.post(reverse('contour:measure_file_model_add'),
                                    {'title' : file_name,
                                     'measure_file' : test_file_simple_uploaded
                                    },
                                    follow=True)
        self.assertContains(response, "scatter plot", status_code = 200)

        # Then share the file with another user. First show the view.
        response = self.client.get(reverse('contour:measure_file_model_update',
                                           kwargs={'pk': 1}),
                                    follow=True)
        self.assertContains(response, "secondary user",
                            status_code = 200)
        # Then post that the file should be shared with a secondary user.
        # Use a non-existing user name, one should be redirected to home and an
        # error message should be shown.
        response = self.client.post(reverse('contour:measure_file_model_update',
                                           kwargs={'pk': 1}),
                                    {'username': 'non_existing_user'},
                                    follow=True)
        self.assertContains(response, "Dashboard",
                            status_code = 200)
        # Use an existing user name, one should be redirected to the overview.
        response = self.client.post(reverse('contour:measure_file_model_update',
                                           kwargs={'pk': 1}),
                                    {'username': 'sabine_mustermann'},
                                    follow=True)
        self.assertContains(response, "Uploaded measurement files",
                            status_code = 200)

        # Finally delete the uploaded file. This servers two purposes:
        # 1. To test it
        # 2. To avoid adding up .csv files in the dir each time the test is run
        response = self.client.get(reverse('contour:measure_file_model_delete',
                                           kwargs={'pk': 1}),
                                   follow=True)
        self.assertContains(response, "Uploaded measurement files",
                            status_code = 200)
