# from markets.models import Trade, Strategy

# from unittest.mock import patch

# from django.test import TestCase, Client
# from django.urls import reverse
# from django.contrib.auth import get_user_model
# from django.core.files.uploadedfile import SimpleUploadedFile

# User = get_user_model()

# class PagesViewsTest(TestCase):
#     def setUp(self):
#         self.client = Client()
#         self.user = User.objects.create_user(
#             username='danitester',
#             email='danitester@abv.com',
#             password='danitester'
#         )

#     def test_home_view(self):
#         response = self.client.get(reverse('pages:home'))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'pages/home.html')

#     def test_profile_view_unauthorized(self):
#         response = self.client.get(reverse('pages:profile'))
#         self.assertEqual(response.status_code, 302)

#     def test_profile_view_authorized(self):
#         self.client.login(username='danitester', password='danitester')

#         Trade.objects.create(
#             user=self.user,
#             ticker='AAPL',
#             trade_type='BUY',
#             amount=100,
#             enter_price='150.00',
#             is_open=True
#         )

#         with patch('pages.views.get_ticker_price') as mock_price:
#             mock_price.return_value = 160.00

#             response = self.client.get(reverse('pages:profile'))

#             self.assertEqual(response.status_code, 200)
#             self.assertTemplateUsed(response, 'pages/profile.html')

#             self.assertIn('open_trades_data', response.context)
#             self.assertEqual(len(response.context['open_trades_data']), 1)
#             self.assertAlmostEqual(
#                 response.context['open_trades_data'][0]['profit_loss_percentage'],
#                 6.67,
#                 places=2
#             )

#     def test_contact_us_view(self):
#         self.client.login(username='testuser', password='testpass123')

#         response = self.client.get(reverse('pages:contact-us'))
#         self.assertEqual(response.status_code, 200)
#         self.assertTemplateUsed(response, 'pages/contact-us.html')

#         with patch('pages.views.mailjet.send.create') as mock_mailjet:
#             post_data = {
#                 'subject': 'Test Subject',
#                 'message': 'Test Message'
#             }
#             response = self.client.post(reverse('pages:contact-us'), post_data)
#             self.assertEqual(response.status_code, 200)
#             mock_mailjet.assert_called_once()

#     def test_import_trades(self):
#         self.client.login(username='testuser', password='testpass123')

#         csv_content = (
#             "SYMBOL,TYPE,AMOUNT,PRICE,DATETIME\n"
#             "AAPL,BUY,100,150.00,2024-01-01 10:00:00"
#         )

#         response = self.client.post(reverse('pages:import-trades'), {
#             'csv_file': SimpleUploadedFile(
#                 'test.csv',
#                 csv_content.encode('utf-8'),
#                 content_type='text/csv'
#             )
#         })

#         self.assertEqual(response.status_code, 302)
#         self.assertEqual(Trade.objects.count(), 1)
#         trade = Trade.objects.first()
#         self.assertEqual(trade.ticker, 'AAPL')
#         self.assertEqual(trade.trade_type, 'BUY')
