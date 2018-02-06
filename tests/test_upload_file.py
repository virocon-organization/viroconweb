from django.test import TestCase, Client
from django.core.urlresolvers import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os

class UploadFileTestCase(TestCase):
    def setUp(self):
        self.test_files_path = os.path.abspath(os.path.join(os.path.dirname( __file__), r'test_files/'))
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

    def test_upload_file(self):
        file_name = '1yeardata_vanem2012pdf_withHeader.csv'
        with open(os.path.join(self.test_files_path , file_name), "rb") as csv_file:
            file_content = csv_file.read()
        test_file = SimpleUploadedFile(file_name, file_content)

        self.client.post(reverse('enviro:measurefiles-add'),
                         {'data' : {
                             'title' : file_name,
                             'measure_file' : file_name
                         },
                          'files' : test_file})

