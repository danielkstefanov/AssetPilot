import uuid
import os

from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import datetime
from newsapi import NewsApiClient
from .models import NewsItem
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from utils.scrape import scrape_news_content
from utils.news_analysis import analyze_sentiment

newsapi = NewsApiClient(api_key=os.environ.get("NEWS_API_KEY"))


@login_required
def news(request):

    news = []
    query_string = request.GET.get("q")

    try:
        if query_string:
            stock_news = newsapi.get_everything(
                q=f'({query_string} OR "{query_string} stock" OR "{query_string} shares")',
                language="en",
            )
        else:
            stock_news = newsapi.get_top_headlines(
                category="business",
                language="en",
                page_size=100,
                page=1,
            )

        for article in stock_news.get("articles", []):
            if all(
                article.get(field)
                for field in ["urlToImage", "title", "description", "content"]
            ):
                news_item = {
                    "id": uuid.uuid5(
                        uuid.NAMESPACE_DNS, str(article["url"].encode("utf-8"))
                    ),
                    "datetime": datetime.strptime(
                        article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "headline": article["title"],
                    "content": None,
                    "summary": article["description"],
                    "image": article["urlToImage"],
                    "url": article["url"],
                    "source": article["source"]["name"],
                }
                news.append(news_item)

                if not NewsItem.objects.filter(id=news_item["id"]).exists():
                    NewsItem.objects.create(**news_item)

    except Exception:
        print("Error while fetching news!")

    paginator = Paginator(news, 10)
    page = request.GET.get("page", 1)
    paginated_news = paginator.page(page)

    featured_news = (
        paginated_news.object_list[:2]
        if len(paginated_news.object_list) >= 2
        else paginated_news.object_list
    )

    regular_news = (
        paginated_news.object_list[2:] if len(paginated_news.object_list) > 2 else []
    )

    context = {
        "featured_news": featured_news,
        "regular_news": regular_news,
        "page_obj": paginated_news,
        "search_query": request.GET.get("q", ""),
    }

    return render(request, "news/news.html", context)


@login_required
def news_details(request, news_id):

    news_item = get_object_or_404(NewsItem, id=news_id)

    if news_item.content is None:
        new_content = scrape_news_content(news_item.url)
        news_analize = analyze_sentiment(news_item.headline, new_content)

        if new_content is not None:
            news_item.content = new_content
            news_item.sentiment_score = Decimal(news_analize["sentiment_score"])
            news_item.is_positive = news_analize["is_positive"]
            news_item.save()

    context = {
        "news": {
            "title": news_item.headline,
            "description": news_item.summary,
            "content": news_item.content,
            "urlToImage": news_item.image,
            "url": news_item.url,
            "source": {"name": news_item.source},
            "publishedAt": news_item.datetime.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sentiment_score": news_item.sentiment_score,
            "is_positive": news_item.is_positive,
        }
    }

    return render(request, "news/news_details.html", context)
