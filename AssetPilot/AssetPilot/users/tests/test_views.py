from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.datastructures import MultiValueDictKeyError

User = get_user_model()


class TestLoginView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.login_url = reverse("users:login")
        self.home_url = reverse("pages:home")

    def test_login_page_loads(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")

    def test_login_success(self):
        response = self.client.post(self.login_url, { "username": "danitester", "password": "danitester"})
        self.assertRedirects(response, self.home_url)

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_login_wrong_password(self):
        response = self.client.post(self.login_url, { "username": "danitester", "password": "notdanitester"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")
        self.assertContains(response, "Invalid username or password")

        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_username(self):
        response = self.client.post(self.login_url, { "username": "notdanitester", "password": "danitester"})

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")
        self.assertContains(response, "Invalid username or password")
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        
    def test_login_missing_username(self):
        with self.assertRaises(MultiValueDictKeyError):
            self.client.post(self.login_url, {"password": "danitester"})

    def test_login_missing_password(self):
        with self.assertRaises(MultiValueDictKeyError):
            self.client.post(self.login_url, {"username": "danitester"})


