import os
from django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from mailjet_rest import Client


def home_view(request):
    return render(request, 'pages/home.html')


# Replace with your Mailjet API credentials
MAILJET_API_KEY = 'your_mailjet_api_key'
MAILJET_API_SECRET = 'your_mailjet_api_secret'
MAILJET_EMAIL = 'assetPilot@abv.bg'


def contact_us_view(request):
    if request.method == 'POST':

        if not request.user.is_authenticated:
            return render(request, 'pages/contact-us.html', {'error': 'You have to be logged in!'})

        subject = request.POST.get('subject')
        message = request.POST.get('message')
        user_email = request.user.email

        if subject and message:
            # Send email using Mailjet
            mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_API_SECRET), version='v3.1')
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": MAILJET_EMAIL,
                            "Name": "AssetPilot"
                        },
                        "To": [
                            {
                                "Email": MAILJET_EMAIL,
                                "Name": "Support"
                            }
                        ],
                        "Subject": subject,
                        "TextPart": f"Message from {user_email}:\n\n{message}",
                    }
                ]
            }
            result = mailjet.send.create(data=data)

            if result.status_code == 200:
                messages.success(request, "Your message has been sent successfully!")
            else:
                messages.error(request, "Failed to send your message. Please try again later.")

            return redirect('contact-us')

    return render(request, 'pages/contact-us.html')
