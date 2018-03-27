from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class ImprintTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_renders_correctly(self):
        response = self.client.get(reverse('info:imprint'), follow=True)
        self.assertContains(response, "Imprint",
                            status_code = 200)
