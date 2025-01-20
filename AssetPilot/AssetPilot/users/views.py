from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("/")
        else:
            return render(
                request, "users/login.html", {"error": "Invalid username or password"}
            )

    return render(request, "users/login.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirm_password = request.POST["confirm_password"]

        if password != confirm_password:
            return render(
                request, "users/register.html", {"error": "Passwords do not match"}
            )

        if User.objects.filter(username=username).exists():
            return render(
                request, "users/register.html", {"error": "Username already exists"}
            )

        if User.objects.filter(email=email).exists():
            return render(
                request, "users/register.html", {"error": "Email already exists"}
            )

        user = User.objects.create_user(
            username=username, email=email, password=password
        )

        user = authenticate(request, username=username, email=email, password=password)
        if user:
            login(request, user)
            return redirect("home")

    return render(request, "users/register.html")


@login_required
def logout_view(request):
    logout(request)
    return redirect("login")
