import os
import stripe
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(View):
    def post(self, request, *args, **kwargs):
        payload = request.body.decode('utf-8')
        print("===============================================")
        print(payload)
        # sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        #
        # # test print
        # print("Stripe signature header:", sig_header)
        # print("Webhook secret:", WEBHOOK_SECRET)
        #
        #
        # try:
        #     event = stripe.Webhook.construct_event(
        #         payload, sig_header, WEBHOOK_SECRET
        #     )
        # except ValueError:
        #     print(" ValueError: payload не JSON")
        #     return HttpResponse(status=400)
        # except stripe.error.SignatureVerificationError:
        #     print(" SignatureVerificationError: підпис не збігається")
        #     return HttpResponse(status=400)
        #
        # if event["type"] == "checkout.session.completed":
        #     session = event["data"]["object"]
        #     print(" Checkout completed:", session)
        #
        # return HttpResponse(status=200)
