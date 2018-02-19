from django.test import TestCase, Client
from django.core.urlresolvers import reverse


class AboutTestCase(TestCase):

    def setUp(self):
        self.client = Client()

    def test_renders_correctly(self):
        response = self.client.get(reverse('contact:about'), follow=True)
        self.assertContains(response, "ViroCon GitHub repository",
                            status_code = 200)
