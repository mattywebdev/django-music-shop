import stripe
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .webhook_service import WebhookValidationError, process_checkout_payment_event


@csrf_exempt
@require_POST
def stripe_webhook(request):
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    if not webhook_secret:
        return JsonResponse({"error": "Webhook is not configured."}, status=503)

    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            signature,
            webhook_secret,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return JsonResponse({"error": "Invalid webhook."}, status=400)

    try:
        result = process_checkout_payment_event(event)
    except WebhookValidationError:
        return JsonResponse({"error": "Webhook data does not match."}, status=400)

    return JsonResponse({"received": True, "result": result})
