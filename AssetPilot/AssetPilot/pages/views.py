import os
from django.shortcuts import render, redirect
from django.contrib import messages
from mailjet_rest import Client

MAILJET_API_KEY = os.environ.get("MAILJET_API_KEY")
MAILJET_API_SECRET = os.environ.get("MAILJET_API_SECRET")
MAILJET_EMAIL = os.environ.get("MAILJET_EMAIL")


def error_404_view(request, exception):
    return render(request, "404.html", status=404)


def home_view(request):
    return render(request, "pages/home.html")


def contact_us_view(request):
    if request.method == "POST":

        print(MAILJET_API_KEY)

        if not request.user.is_authenticated:
            return render(
                request, "pages/contact-us.html", {"error": "You have to be logged in!"}
            )

        subject = request.POST.get("subject")
        message = request.POST.get("message")
        user_email = request.user.email

        if subject and message:
            mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version="v3.1")
            data = {
                "Messages": [
                    {
                        "From": {"Email": MAILJET_EMAIL, "Name": "Asset Pilot"},
                        "To": [{"Email": MAILJET_EMAIL, "Name": "Support Team"}],
                        "Subject": subject,
                        "TextPart": f"Message from {user_email}:\n\n{message}",
                    }
                ]
            }
            result = mailjet.send.create(data=data)

            if result.status_code == 200:
                messages.success(request, "Your message has been sent successfully!")
            else:
                messages.error(
                    request, "Failed to send your message. Please try again later."
                )

            return redirect("contact-us")

    return render(request, "pages/contact-us.html")
