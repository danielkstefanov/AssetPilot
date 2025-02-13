from django.test import TestCase
from news.models import NewsItem
from django.db import IntegrityError, transaction
from datetime import datetime


class NewsItemModelTest(TestCase):

    def setUp(self):
        self.news_item = NewsItem.objects.create(
            headline="Headline",
            summary="Summary",
            content="Content",
            sentiment_score=0.5,
            is_positive=True,
            image="https://image",
            url="https://source",
            datetime=datetime.now(),
        )

    def test_news_item_creation(self):
        self.assertEqual(self.news_item.headline, "Headline")
        self.assertEqual(self.news_item.summary, "Summary")
        self.assertEqual(self.news_item.content, "Content")
        self.assertEqual(self.news_item.sentiment_score, 0.5)
        self.assertEqual(self.news_item.is_positive, True)
        self.assertEqual(self.news_item.image, "https://image")
        self.assertEqual(self.news_item.url, "https://source")

    def test_news_item_sentiment_score_range(self):

        news_item = NewsItem(
            headline="Headline",
            summary="Summary",
            content="Content",
            sentiment_score=101,
            is_positive=True,
            image="https://image",
            url="https://source",
            datetime=datetime.now(),
        )

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                news_item.save()

        news_item.sentiment_score = -101
        news_item.is_positive = False

        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                news_item.save()
    
    def test_news_item_sentiment_true(self):
        news_item = NewsItem(
            headline="Headline",
            summary="Summary",
            content="Content",
            sentiment_score=50,
            is_positive=False,
            datetime=datetime.now(),
        )

        with self.assertRaises(IntegrityError):
            news_item.save()

    def test_news_item_sentiment_false(self):
        news_item = NewsItem(
            headline="Headline",
            summary="Summary",
            content="Content",
            sentiment_score=-50,
            is_positive=True,
            datetime=datetime.now(),
        )

        with self.assertRaises(IntegrityError):
            news_item.save()
