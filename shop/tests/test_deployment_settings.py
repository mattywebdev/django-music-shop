from pathlib import Path
from tempfile import gettempdir

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from music_shop.settings import validate_production_configuration


class ProductionConfigurationTests(SimpleTestCase):
    def configuration(self, **overrides):
        root = Path(gettempdir()).resolve() / "music-shop-deployment-test"
        configuration = {
            "debug": False,
            "secret_key": "s" * 50,
            "stripe_secret_key": "sk_test_placeholder",
            "stripe_webhook_secret": "whsec_placeholder",
            "stripe_currency": "gbp",
            "media_root": root / "media",
            "static_root": root / "staticfiles",
            "private_media_root": root / "private_media",
        }
        configuration.update(overrides)
        return configuration

    def test_valid_sandbox_production_configuration_is_accepted(self):
        validate_production_configuration(**self.configuration())

    def test_debug_configuration_does_not_require_production_secrets(self):
        validate_production_configuration(
            **self.configuration(
                debug=True,
                secret_key="",
                stripe_secret_key="",
                stripe_webhook_secret="",
            )
        )

    def test_insecure_production_secrets_and_currency_are_rejected(self):
        with self.assertRaises(ImproperlyConfigured) as raised:
            validate_production_configuration(
                **self.configuration(
                    secret_key="short",
                    stripe_secret_key="sk_live_not_allowed",
                    stripe_webhook_secret="",
                    stripe_currency="usd",
                )
            )

        message = str(raised.exception)
        self.assertIn("DJANGO_SECRET_KEY", message)
        self.assertIn("test-mode", message)
        self.assertIn("STRIPE_WEBHOOK_SECRET", message)
        self.assertIn("STRIPE_CURRENCY", message)

    def test_relative_private_media_root_is_rejected(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DJANGO_PRIVATE_MEDIA_ROOT must be an absolute path",
        ):
            validate_production_configuration(
                **self.configuration(private_media_root=Path("private_media"))
            )

    def test_private_media_root_inside_public_media_root_is_rejected(self):
        configuration = self.configuration()
        configuration["private_media_root"] = (
            Path(configuration["media_root"]) / "private"
        )

        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "DJANGO_PRIVATE_MEDIA_ROOT must not overlap MEDIA_ROOT",
        ):
            validate_production_configuration(**configuration)
