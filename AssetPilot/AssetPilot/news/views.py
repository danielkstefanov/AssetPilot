from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from markets.models import Trade
from datetime import datetime, timedelta
import os
from newsapi import NewsApiClient
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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
                sort_by="publishedAt",
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
                    "id": hash(article["url"]),
                    "datetime": datetime.strptime(
                        article["publishedAt"], "%Y-%m-%dT%H:%M:%SZ"
                    ),
                    "headline": article["title"],
                    "summary": article["description"],
                    "content": article["content"],
                    "image": article["urlToImage"],
                    "url": article["url"],
                    "source": article["source"]["name"],
                }
                news.append(news_item)

    except Exception:
        print("Error while fetching news!")

    paginator = Paginator(news, 10)
    page = request.GET.get("page", 1)

    try:
        paginated_news = paginator.page(page)
    except PageNotAnInteger:
        paginated_news = paginator.page(1)
    except EmptyPage:
        paginated_news = paginator.page(paginator.num_pages)

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
def news_detail(request, news_id):
    all_news = request.session.get("all_news", [])
    news_item = next((item for item in all_news if item["id"] == news_id), None)

    if not news_item:
        return redirect("news")

    news_item["datetime"] = datetime.fromisoformat(news_item["datetime"])

    context = {
        "news": news_item,
    }
    return render(request, "news/news_detail.html", context)
