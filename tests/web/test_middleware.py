import pytest
from django.contrib.auth.models import AnonymousUser
from djpaypal.models import BillingAgreement
from rest_framework.test import APIRequestFactory

from hsreplaynet.web.middleware import PayPalSyncMiddleware, UserActivityMiddleware


class TestUserActivityMiddleware:

	def setup_method(self):
		self.middleware = UserActivityMiddleware(lambda request: "Test Response")
		self.request_factory = APIRequestFactory()

	def test_call_unauthenticated(self):
		request = self.request_factory.get("/")
		request.user = AnonymousUser()

		assert self.middleware(request) == "Test Response"

	def test_call_authenticated(self, user):
		request = self.request_factory.get("/")
		request.user = user

		assert self.middleware(request) == "Test Response"
		assert user.last_site_activity is not None


@pytest.mark.django_db
class TestPayPalSyncMiddleware:

	def mock_find_and_sync(self, id):
		ba = BillingAgreement.objects.get(id=id)
		ba.state = "Active"
		ba.save()

	def setup_method(self):
		self.middleware = PayPalSyncMiddleware(lambda request: "Test Response")
		self.request_factory = APIRequestFactory()

	def test_call_unauthenticated(self, mocker):
		request = self.request_factory.get("/")
		request.user = AnonymousUser()

		assert self.middleware(request) == "Test Response"

	def test_call_authenticated(self, user, mocker):
		BillingAgreement.objects.create(
			id="ID",
			livemode=True,
			start_date="2018-01-01 00:00",
			user=user,
			state="Pending",
			payer={},
			agreement_details={},
			description="foo",
			shipping_address="foo",
			plan={}
		)
		mocker.patch(
			"djpaypal.models.BillingAgreement.find_and_sync",
			self.mock_find_and_sync
		)

		request = self.request_factory.get("/")
		request.user = user

		assert self.middleware(request) == "Test Response"
		assert BillingAgreement.objects.get(user=user).state == "Active"
