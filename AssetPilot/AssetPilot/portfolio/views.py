from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def portfolio(request):
    return render(request, "portfolio/portfolio.html")
