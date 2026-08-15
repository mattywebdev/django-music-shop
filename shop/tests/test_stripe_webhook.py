import json
from decimal import Decimal
from unittest.mock import patch

import stripe
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from shop.models import Order, OrderItem, StripeEvent


@override_settings(STRIPE_WEBHOOK_SECRET="whsec_test_example", STRIPE_CURRENCY="gbp")
class StripeWebhookTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "webhook-buyer", email="buyer@example.com", password="p"
        )

    def setUp(self):
        self.order = Order.objects.create(
            user=self.user,
            status="pending",
            total_amount=Decimal("9.99"),
            stripe_checkout_session_id="cs_test_webhook",
        )
        OrderItem.objects.create(
            order=self.order,
            item_type="album",
            item_id=1,
            title="Webhook Album",
            quantity=1,
            unit_price=Decimal("9.99"),
        )

    def event(self, event_id="evt_test_paid", event_type="checkout.session.completed", **changes):
        session = {
            "id": "cs_test_webhook",
            "client_reference_id": str(self.order.pk),
            "metadata": {
                "order_id": str(self.order.pk),
                "user_id": str(self.user.pk),
            },
            "mode": "payment",
            "payment_status": "paid",
            "currency": "gbp",
            "amount_total": 999,
            "payment_intent": "pi_test_webhook",
        }
        session.update(changes)
        return {
            "id": event_id,
            "type": event_type,
            "data": {"object": session},
        }

    def post_verified_event(self, event):
        with patch(
            "shop.webhook_views.stripe.Webhook.construct_event",
            return_value=event,
        ) as construct_event:
            response = self.client.post(
                reverse("stripe_webhook"),
                data=json.dumps(event),
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="t=1,v1=test",
            )
        self.assertEqual(construct_event.call_args.args[0], response.wsgi_request.body)
        self.assertEqual(construct_event.call_args.args[1], "t=1,v1=test")
        self.assertEqual(construct_event.call_args.args[2], "whsec_test_example")
        return response

    def test_valid_completed_event_marks_pending_order_paid(self):
        response = self.post_verified_event(self.event())

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")
        self.assertIsNotNone(self.order.paid_at)
        self.assertEqual(self.order.stripe_payment_intent_id, "pi_test_webhook")
        self.assertTrue(
            StripeEvent.objects.filter(
                event_id="evt_test_paid",
                event_type="checkout.session.completed",
                order=self.order,
            ).exists()
        )

    def test_async_payment_succeeded_marks_order_paid(self):
        response = self.post_verified_event(self.event(
            event_id="evt_test_async",
            event_type="checkout.session.async_payment_succeeded",
        ))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "paid")

    def test_duplicate_event_delivery_is_harmless(self):
        event = self.event()
        self.post_verified_event(event)
        self.order.refresh_from_db()
        original_paid_at = self.order.paid_at

        response = self.post_verified_event(event)

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.paid_at, original_paid_at)
        self.assertEqual(StripeEvent.objects.filter(event_id="evt_test_paid").count(), 1)

    def test_second_success_event_does_not_reset_paid_at(self):
        self.post_verified_event(self.event())
        self.order.refresh_from_db()
        original_paid_at = self.order.paid_at

        response = self.post_verified_event(self.event(
            event_id="evt_test_second",
            event_type="checkout.session.async_payment_succeeded",
        ))

        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.paid_at, original_paid_at)
        self.assertEqual(self.order.stripe_events.count(), 2)

    def test_invalid_signature_does_not_modify_order(self):
        with patch(
            "shop.webhook_views.stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError("bad signature", "sig"),
        ):
            response = self.client.post(
                reverse("stripe_webhook"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="invalid",
            )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self.assertFalse(StripeEvent.objects.exists())

    def test_malformed_payload_does_not_modify_order(self):
        with patch(
            "shop.webhook_views.stripe.Webhook.construct_event",
            side_effect=ValueError("invalid JSON"),
        ):
            response = self.client.post(
                reverse("stripe_webhook"),
                data=b"not-json",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="test",
            )
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_wrong_order_or_session_metadata_does_not_mark_paid(self):
        invalid_events = [
            self.event(event_id="evt_wrong_session", id="cs_test_other"),
            self.event(event_id="evt_wrong_reference", client_reference_id="999999"),
            self.event(event_id="evt_wrong_metadata", metadata={
                "order_id": "999999", "user_id": str(self.user.pk)
            }),
        ]
        for event in invalid_events:
            with self.subTest(event_id=event["id"]):
                response = self.post_verified_event(event)
                self.assertEqual(response.status_code, 400)
                self.order.refresh_from_db()
                self.assertEqual(self.order.status, "pending")
        self.assertFalse(StripeEvent.objects.exists())

    def test_wrong_amount_does_not_mark_paid(self):
        response = self.post_verified_event(self.event(amount_total=998))
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_wrong_currency_does_not_mark_paid(self):
        response = self.post_verified_event(self.event(currency="usd"))
        self.assertEqual(response.status_code, 400)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")

    def test_completed_but_unpaid_session_waits_for_async_success(self):
        response = self.post_verified_event(self.event(payment_status="unpaid"))
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self.assertFalse(StripeEvent.objects.exists())

    def test_irrelevant_event_is_acknowledged_without_changes(self):
        event = {"id": "evt_irrelevant", "type": "customer.created", "data": {"object": {}}}
        response = self.post_verified_event(event)
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self.assertFalse(StripeEvent.objects.exists())

    def test_success_url_cannot_mark_order_paid(self):
        self.client.login(username="webhook-buyer", password="p")
        response = self.client.get(
            reverse("success") + "?session_id=cs_test_webhook"
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "pending")
        self.assertIsNone(self.order.paid_at)
