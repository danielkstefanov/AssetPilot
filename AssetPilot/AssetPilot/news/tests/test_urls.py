from django.test import TestCase
from django.urls import reverse, resolve
from news.views import news, news_details
import uuid


class NewsURLTests(TestCase):

    def test_news_url_resolves(self):
        url = reverse("news:news")
        self.assertEqual(resolve(url).func, news)

    def test_news_details_url_resolves(self):
        news_id = uuid.uuid4()
        url = reverse("news:news_details", kwargs={"news_id": news_id})
        self.assertEqual(resolve(url).func, news_details)

    def test_news_details_url_format(self):
        news_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
        url = reverse("news:news_details", kwargs={"news_id": news_id})
        expected_url = f"/news/details/{news_id}/"
        self.assertEqual(url, expected_url)
