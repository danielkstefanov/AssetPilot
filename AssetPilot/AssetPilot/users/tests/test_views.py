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
        response = self.client.post(
            self.login_url, {"username": "danitester", "password": "danitester"}
        )
        self.assertRedirects(response, self.home_url)

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_login_wrong_password(self):
        response = self.client.post(
            self.login_url, {"username": "danitester", "password": "notdanitester"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/login.html")
        self.assertContains(response, "Invalid username or password")

        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_wrong_username(self):
        response = self.client.post(
            self.login_url, {"username": "notdanitester", "password": "danitester"}
        )

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


class TestRegisterView(TestCase):
    def setUp(self):
        self.register_url = reverse("users:register")
        self.home_url = reverse("pages:home")

        self.valid_data = {
            "username": "danitester2",
            "email": "danitester2@abv.bg",
            "password": "danitester2",
            "confirm_password": "danitester2",
        }

        self.existing_user = User.objects.create_user(
            username="danitester",
            email="danitester@abv.bg",
            password="danitester",
        )

    def test_register_page_loads(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")

    def test_register_success(self):
        response = self.client.post(self.register_url, self.valid_data)
        self.assertRedirects(response, self.home_url)

        self.assertTrue(User.objects.filter(username="danitester2").exists())
        user = User.objects.get(username="danitester2")
        self.assertEqual(user.email, "danitester2@abv.bg")

        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, user)

    def test_register_duplicate_username(self):
        data = self.valid_data
        data["username"] = "danitester"

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
        self.assertContains(response, "Username already exists!")

        self.assertEqual(User.objects.count(), 1)

    def test_register_password_mismatch(self):
        data = self.valid_data
        data["confirm_password"] = "differentpass123"

        response = self.client.post(self.register_url, data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "users/register.html")
        self.assertContains(response, "Passwords do not match!")
        self.assertEqual(User.objects.count(), 1)

    def test_register_already_authenticated(self):
        self.client.login(username="danitester", password="danitester")
        response = self.client.get(self.register_url)
        self.assertRedirects(response, self.home_url)
        response = self.client.post(self.register_url, self.valid_data)
        self.assertRedirects(response, self.home_url)
        self.assertEqual(User.objects.count(), 1)


class TestLogoutView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.bg", password="danitester"
        )

        self.logout_url = reverse("users:logout")
        self.login_url = reverse("users:login")

    def test_logout_requires_login(self):
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, f"{self.login_url}?next={self.logout_url}")

    def test_logout_success(self):
        self.client.login(username="danitester", password="danitester")
        self.assertTrue(self.client.session.get("_auth_user_id"))
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, self.login_url)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertFalse(self.client.session.get("_auth_user_id"))
