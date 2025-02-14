import uuid
from datetime import datetime
from decimal import Decimal

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User

from unittest.mock import patch

from news.models import NewsItem

ARTICLE_DATA = {
    "articles": [
        {
            "title": "Headline 1",
            "description": "Summary 1",
            "content": "Content 1",
            "urlToImage": "https://test.com/image1.jpg",
            "url": "https://test.com/article1",
            "publishedAt": "2024-03-20T12:00:00Z",
            "source": {"name": "Source"},
        },
        {
            "title": "Headline 2",
            "description": "Summary 2",
            "content": "Content 2",
            "urlToImage": "https://test.com/image2.jpg",
            "url": "https://test.com/article2",
            "publishedAt": "2024-03-20T13:00:00Z",
            "source": {"name": "Source"},
        },
    ]
}


class TestNewsPage(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )
        self.client = Client()

    def test_news_view_requires_login(self):
        response = self.client.get(reverse("news:news"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_news_view_authenticated(self):
        self.client.login(username="danitester", password="danitester")

        with patch("news.views.newsapi.get_top_headlines", return_value=ARTICLE_DATA):
            response = self.client.get(reverse("news:news"))

            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "news/news.html")

            self.assertTrue("featured_news" in response.context)
            self.assertTrue("regular_news" in response.context)
            self.assertEqual(NewsItem.objects.count(), 2)

    def test_news_view_with_search(self):
        self.client.login(username="danitester", password="danitester")

        with patch(
            "news.views.newsapi.get_everything", return_value=ARTICLE_DATA
        ) as mock_get_news:
            response = self.client.get(reverse("news:news") + "?q=TSLA")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["search_query"], "TSLA")

            mock_get_news.assert_called_with(
                q='(TSLA OR "TSLA stock" OR "TSLA shares")', language="en"
            )
            self.assertEqual(NewsItem.objects.count(), 2)

    def test_news_view_pagination(self):
        self.client.login(username="danitester", password="danitester")

        articles = []
        for i in range(15):
            articles.append(
                {
                    "title": f"Headline {i}",
                    "description": f"Summary {i}",
                    "content": f"Content {i}",
                    "urlToImage": f"https://test.com/image{i}.jpg",
                    "url": f"https://test.com/article{i}",
                    "publishedAt": "2024-03-20T12:00:00Z",
                    "source": {"name": "Source"},
                }
            )

        with patch(
            "news.views.newsapi.get_top_headlines", return_value={"articles": articles}
        ) as mock_get_news:
            response = self.client.get(reverse("news:news"))
            self.assertEqual(len(response.context["page_obj"].object_list), 10)

            response = self.client.get(reverse("news:news") + "?page=2")
            self.assertEqual(len(response.context["page_obj"].object_list), 5)

    def test_news_view_api_error(self):
        self.client.login(username="danitester", password="danitester")

        with patch(
            "news.views.newsapi.get_top_headlines", side_effect=Exception("API Error")
        ):
            response = self.client.get(reverse("news:news"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.context["featured_news"]), 0)
            self.assertEqual(len(response.context["regular_news"]), 0)


class TestNewsDetailsPage(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="danitester", email="danitester@abv.com", password="danitester"
        )

        self.news_item = NewsItem.objects.create(
            id=uuid.uuid4(),
            headline="Test Headline",
            summary="Test Summary",
            content=None,
            image="https://test.com/image.jpg",
            url="https://test.com/article",
            source="Test Source",
            datetime=datetime.now(),
            sentiment_score=None,
            is_positive=None,
        )

    def test_news_details_requires_login(self):
        response = self.client.get(
            reverse("news:news_details", kwargs={"news_id": self.news_item.id})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_news_details_with_existing_content(self):
        self.client.login(username="danitester", password="danitester")

        self.news_item.content = "Existing Content"
        self.news_item.sentiment_score = Decimal("0.5")
        self.news_item.is_positive = True
        self.news_item.save()

        response = self.client.get(
            reverse("news:news_details", kwargs={"news_id": self.news_item.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "news/news_details.html")

        news = response.context["news"]
        self.assertEqual(news["title"], "Test Headline")
        self.assertEqual(news["content"], "Existing Content")
        self.assertEqual(news["sentiment_score"], Decimal("0.5"))
        self.assertTrue(news["is_positive"])

    def test_news_details_with_content_scraping(self):
        self.client.login(username="danitester", password="danitester")

        scraped_content = "Scraped news content"
        sentiment_analysis = {"sentiment_score": 0.8, "is_positive": True}

        with patch("news.views.scrape_news_content", return_value=scraped_content):
            with patch("news.views.analyze_sentiment", return_value=sentiment_analysis):
                response = self.client.get(
                    reverse("news:news_details", kwargs={"news_id": self.news_item.id})
                )

                self.assertEqual(response.status_code, 200)

                self.news_item.refresh_from_db()
                self.assertEqual(self.news_item.content, scraped_content)
                self.assertAlmostEqual(self.news_item.sentiment_score, Decimal("0.8"))
                self.assertTrue(self.news_item.is_positive)

    def test_news_details_invalid_id(self):
        self.client.login(username="danitester", password="danitester")

        response = self.client.get(
            reverse("news:news_details", kwargs={"news_id": uuid.uuid4()})
        )
        
        self.assertEqual(response.status_code, 404)

    def test_news_details_scraping_failure(self):
        self.client.login(username="danitester", password="danitester")
        
        test_news = NewsItem.objects.create(
            id=uuid.uuid4(),
            headline="Test Headline",
            summary="Test Summary",
            content="Content",
            image="https://test.com/image.jpg",
            url="https://test.com/article",
            source="Test Source",
            datetime=datetime.now(),
            sentiment_score=None,
            is_positive=None,
        )

        with patch("news.views.scrape_news_content", return_value=None):
            with patch("news.views.analyze_sentiment") as mock_analyze:

                response = self.client.get(
                    reverse("news:news_details", kwargs={"news_id": test_news.id})
                )
                self.assertEqual(response.status_code, 200)

                mock_analyze.assert_not_called()

                test_news.refresh_from_db()
                self.assertIsNone(test_news.sentiment_score)
                self.assertIsNone(test_news.is_positive)
