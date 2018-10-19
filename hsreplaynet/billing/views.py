from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, SuspiciousOperation
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import is_safe_url
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.views.generic import View
from djstripe.enums import SubscriptionStatus
from djstripe.settings import STRIPE_LIVE_MODE
from stripe.error import CardError, InvalidRequestError

from hsreplaynet.utils.influx import influx_metric
from hsreplaynet.web.templatetags.web_extras import pretty_card
from hsreplaynet.web.views import SimpleReactView

from .models import CancellationRequest


STRIPE_DEBUG = not STRIPE_LIVE_MODE and settings.DEBUG


class PaymentsMixin:
	def get_customer(self):
		"""
		Returns the user's Stripe customer object, or None for logged out users.
		"""
		if self.request.user.is_authenticated:
			return self.request.user.stripe_customer

	def can_cancel(self, customer):
		"""
		Return whether a customer is allowed to cancel (at end of period).
		"""
		if not customer or not customer.active_subscriptions.exists():
			# Safeguard
			return False

		# We only allow end-of-period cancel if the current subscription is active.
		return customer.active_subscriptions.exists()

	def has_subscription_past_due(self, customer):
		return customer.subscriptions.filter(status=SubscriptionStatus.past_due).exists()

	def can_cancel_immediately(self, customer):
		"""
		Returns whether a customer is allowed to cancel immediately.
		"""
		if self.has_subscription_past_due(customer):
			# Can always do an immediate cancel when past due
			return True

		if not customer or not customer.active_subscriptions.exists():
			# Safeguard
			return False

		if STRIPE_DEBUG:
			# In Stripe debug mode, we always allow immediate cancel.
			return True

		# Otherwise, we only allow immediate cancel if the subscription is not active.
		for subscription in customer.active_subscriptions.all():
			if not subscription.is_valid():
				return True

		return False

	def can_remove_payment_methods(self, customer):
		"""
		Returns whether a customer is allowed to remove their payment methods.

		Will always be True if more than one payment method is available.
		Will be False if there is at least one active subscription, which is
		not scheduled to be cancelled.
		"""
		sources_count = customer.legacy_cards.count() + customer.sources_v3.count()
		if sources_count > 1:
			return True

		return not customer.active_subscriptions.filter(
			cancel_at_period_end=False
		).exists()

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)

		# Will be None if the user is not authenticated
		customer = self.get_customer()
		context["customer"] = customer

		if customer:
			context["currency"] = customer.currency
			context["can_cancel"] = self.can_cancel(customer)
			context["can_cancel_immediately"] = self.can_cancel_immediately(customer)
			context["has_subscription_past_due"] = self.has_subscription_past_due(customer)
		else:
			context["currency"] = "usd"

		return context


class BillingView(LoginRequiredMixin, PaymentsMixin, SimpleReactView):
	title = "Billing"
	bundle = "account_billing"
	base_template = "account/base.html"

	def _clean_currency_amount(self, value):
		"""
		Stripe-format compatibility shim.
		Converts dj-stripe Decimal objects into cent-accuracy integers.
		"""
		from decimal import Decimal
		if isinstance(value, Decimal):
			return int(value * 100)
		return value

	def get_react_context(self):
		customer = self.get_customer()
		assert customer  # This page is not accessible to non-customers...

		stripe = {
			"can_cancel": self.can_cancel(customer),
			"can_cancel_immediately": self.can_cancel_immediately(customer),
			"can_remove_payment_methods": self.can_remove_payment_methods(customer),
			"credits": customer.credits,
			"currency": customer.currency or "usd",
			"pending_charges": customer.pending_charges,
		}

		if customer.default_source:
			stripe["default_source"] = customer.default_source.stripe_id

		if customer.coupon:
			stripe["coupon"] = customer.coupon.human_readable

		try:
			stripe["next_payment_attempt"] = customer.invoices.latest("date").next_payment_attempt
		except ObjectDoesNotExist:
			pass

		stripe["payment_methods"] = []
		for card in customer.legacy_cards.all():
			stripe["payment_methods"].append({
				"type": "legacy_card",
				"id": card.stripe_id,
				"name": pretty_card(card),
				"brand": card.brand,
				"exp_month": card.exp_month,
				"exp_year": card.exp_year,
				"last4": card.last4,
			})

		for source in customer.sources_v3.all():
			stripe["payment_methods"].append({
				"type": "source",
				"id": source.stripe_id,
				"name": pretty_card(source),
				"brand": source.source_data["brand"],
				"exp_month": source.source_data["exp_month"],
				"exp_year": source.source_data["exp_year"],
				"last4": source.source_data["last4"],
			})

		stripe["invoices"] = []
		for invoice in customer.invoices.all():
			stripe["invoices"].append({
				"id": invoice.stripe_id,
				"number": invoice.number,
				"date": invoice.date,
				"currency": invoice.currency,
				"amount_due": self._clean_currency_amount(invoice.amount_due),
				"amount_paid": self._clean_currency_amount(invoice.amount_paid),
				"amount_remaining": self._clean_currency_amount(invoice.amount_remaining),
				"invoice_pdf": invoice.invoice_pdf,
				"hosted_invoice_url": invoice.hosted_invoice_url,
				"period_start": invoice.period_start,
				"period_end": invoice.period_end,
				"paid": invoice.paid,
				"receipt_number": invoice.receipt_number,
				"subtotal": self._clean_currency_amount(invoice.subtotal),
				"total": self._clean_currency_amount(invoice.total),
				"forgiven": invoice.forgiven,
				"closed": invoice.closed,
				"next_payment_attempt": invoice.next_payment_attempt,
				"items": [str(item) for item in invoice.invoiceitems.all()],
			})

		stripe["subscriptions"] = []
		for subscription in customer.valid_subscriptions.all():
			if subscription.plan.amount and not subscription.cancel_at_period_end:
				stripe["has_upcoming_payment"] = True

			stripe["subscriptions"].append({
				"id": subscription.stripe_id,
				"status": subscription.status,
				"cancel_at_period_end": subscription.cancel_at_period_end,
				"current_period_start": subscription.current_period_start,
				"current_period_end": subscription.current_period_end,
				"start": subscription.start,
				"trial_start": subscription.trial_start,
				"trial_end": subscription.trial_end,
				"plan": {
					"id": subscription.plan.id,
					"amount": subscription.plan.amount,
					"name": str(subscription.plan),
					"price": subscription.plan.human_readable_price,
				},
			})

		paypal = {}
		if self.request.user.is_paypal_premium:
			paypal["subscribed"] = True
			paypal["end_of_period"] = self.request.user.paypal_end_of_cancellation_period

		return {
			"paypal": paypal,
			"stripe": stripe,
			"urls": {
				"cancel": reverse("premium_cancel"),
				"update_card": reverse("billing_update_card"),
				"subscribe": reverse("premium_subscribe"),
				"paypal_manage": (
					"https://www.paypal.com/cgi-bin/webscr?cmd=_manage-paylist"
				),
			}
		}


class SubscribeView(LoginRequiredMixin, PaymentsMixin, View):
	success_url = reverse_lazy("billing_methods")

	def process_checkout_form(self, customer):
		# The token represents the customer's payment method
		token = self.request.POST.get("stripeToken", "")
		if not token.startswith(("tok_", "src_")):
			# We either didn't get a token, or it was malformed. Discard outright.
			raise SuspiciousOperation("Missing or invalid Stripe token")

		try:
			# Saving the token as a payment method will create the payment source for us.
			customer.add_card(token)
		except InvalidRequestError:
			# Most likely, we got a bad token (eg. bad request)
			# This is logged by Stripe.
			messages.error(self.request, _("Error adding payment card"))
			return False
		except CardError:
			# Card was declined.
			messages.error(self.request, _("Your card was declined. Please use a different card."))
			return False

		# Stripe Checkout supports capturing email.
		# We ask for it if we don't have one yet.
		email = self.request.POST.get("stripeEmail")
		if email and not self.request.user.email:
			# So if the user doesn't have an email, we set it to the stripe email.
			try:
				# First we attach the email as an EmailAddress to the account
				# confirm=True will send an email confirmation
				EmailAddress.objects.add_email(
					self.request, self.request.user, email, confirm=True
				)
			except IntegrityError:
				messages.error(self.request, _(
					"That email address is associated with another account. "
					"If you'd like to merge accounts, please contact us!"
				))
				return False
			# Then we set it on the account object itself
			self.request.user.email = email
			self.request.user.save()

		# Let's attach the email we got to the Stripe customer object as well
		email = email or self.request.user.email
		if email:
			# Retrieve the Stripe customer object from the API
			cus = customer.api_retrieve()
			# We skip the API call if it's a noop
			if cus.email != email:
				cus.email = email
				# Write the results to the API
				cus.save()

		return True

	def handle_subscribe(self, customer):
		if customer.valid_subscriptions.exists():
			# The customer is already subscribed

			if customer.valid_subscriptions.count() > 1:
				# The customer is already in an error state -- this should not happen.
				messages.error(
					self.request, _("You have multiple subscriptions. Please contact us.")
				)
				return False

			subscription = customer.subscription

			if subscription.cancel_at_period_end:
				# The customer's subscription was canceled and is now being re-activated
				try:
					subscription.reactivate()
				except InvalidRequestError:
					# Maybe the subscription already ran out.
					# Sync the subscriptions and display an error.
					customer._sync_subscriptions()
					messages.error(self.request, _("Your subscription has expired."))
					return False
				return True

			if subscription.status == SubscriptionStatus.past_due:
				messages.error(self.request, _(
					"Your current subscription is still active. "
					"If you are having billing issues, please contact us!"
				))

			messages.error(self.request, _("You are already subscribed!"))
			return False

		lazy_discounts = customer.subscriber.lazy_discounts.filter(used=False)
		if lazy_discounts.exists():
			for discount in lazy_discounts:
				discount.apply()

			# Refresh customer
			customer = customer.__class__.objects.get(pk=customer)

		# The Stripe ID of the plan should be included in the POST
		plan_id = self.request.POST.get("plan")
		# Have to check that it's a plan that users can subscribe to.
		if plan_id not in (settings.MONTHLY_PLAN_ID, settings.SEMIANNUAL_PLAN_ID):
			raise SuspiciousOperation("Invalid plan ID (%r)" % (plan_id))

		try:
			# Attempt to subscribe the customer to the plan
			# Note on `charge_immediately`:
			# This is a misnomer in dj-stripe. The way we use subscriptions,
			# customers are immediately charged by default.
			# If set to True, we will attempt to send an Invoice immediately.
			# This is not the behaviour we want; it will error, there is nothing
			# to invoice as it's done automatically by Stripe.
			customer.subscribe(plan_id, charge_immediately=False)
		except InvalidRequestError:
			# Most likely, bad form data. This will be logged by Stripe.
			messages.error(self.request, _("Could not process subscription."))
			return False
		except CardError as e:
			return self.handle_card_error(e)

		if customer.coupon:
			# HACK: If the customer has a coupon attached and the coupon is
			# now redeemed, a customer.discount webhook does not fire.
			# We force a customer resync to prevent this.
			data = customer.api_retrieve()
			customer.__class__.sync_from_stripe_data(data)

		return True

	def handle_card_error(self, e):
		if e.code in ("do_not_honor", "transaction_not_allowed"):
			# Generic unknown decline reason
			message = _("Your card declined the charge. Please contact your bank for information.")
		elif e.code == "currency_not_supported":
			message = _("Your card does not support payments in USD. Please try a different card.")
		elif e.code == "card_velocity_exceeded":
			message = _("Your card has exceeded its credit limit. Please use a different one.")
		elif e.code == "insufficient_funds":
			message = _("Your card has insufficient funds to proceed.")
		else:
			# Card was declined for some other reason
			message = _(
				"Your card was declined, you have not been charged. "
				"Please try a different card; contact us if this persists."
			)
		messages.error(self.request, message)
		return False

	def get_success_url(self):
		success_url = self.request.GET.get("next", "")
		if success_url and is_safe_url(success_url, allowed_hosts=None):
			return success_url
		return self.success_url

	def post(self, request):
		self.request = request
		# Get the customer first so we can reuse it
		customer = self.get_customer()

		token_type = request.POST.get("stripeTokenType", "")
		if token_type == "source":
			self.process_checkout_form(customer)
		elif token_type:
			raise NotImplementedError("Unknown token type: %r" % (token_type))

		if "plan" in request.POST:
			# Optionally, a plan can be specified. We attempt subscribing to it if there is one.
			if self.handle_subscribe(customer):

				# Null out the premium checkout timestamp so that we don't remind the user to
				# complete the checkout process.

				request.user.last_premium_checkout = None
				request.user.save()

				messages.success(self.request, _("You are now subscribed!"))

		return redirect(self.get_success_url())


class CancelSubscriptionView(LoginRequiredMixin, PaymentsMixin, View):
	success_url = reverse_lazy("billing_methods")

	def fail(self, message):
		message += _(" Please contact us if you are receiving this in error.")
		messages.error(self.request, message)
		return False

	def handle_form(self, request):
		if self.customer.active_subscriptions.count() > 1:
			return self.fail(_("You have multiple subscriptions - something is wrong."))

		subscription = self.customer.subscription

		if not subscription:
			# The customer is not subscribed
			return self.fail(_("You are not subscribed."))

		# Whether the cancellation has effect at the end of the period or immediately
		# True by default (= the subscription remains, will cancel once it ends)
		at_period_end = True

		# Even though both buttons might be shown at once, we will only respect the one
		# that was actually clicked
		how_to_cancel = request.POST.get("cancel")
		if how_to_cancel == "at_period_end":
			pass
		elif how_to_cancel == "immediately":
			if self.can_cancel_immediately(self.customer):
				at_period_end = False
			else:
				return self.fail(_("Your subscription cannot be canceled immediately."))
		else:
			return self.fail(_("Could not cancel your subscription."))

		CancellationRequest.objects.create(
			user=request.user,
			subscription_id=self.customer.subscription.stripe_id,
			reasons={
				k: (True if v == "on" else v) for k, v in request.POST.items() if k.startswith("r-")
			}
		)
		messages.info(self.request, _("Your subscription has been cancelled."))

		self.customer.subscription.cancel(at_period_end=at_period_end)
		return True

	def post(self, request):
		self.customer = self.get_customer()
		self.handle_form(request)
		return redirect(self.success_url)


class UpdateCardView(LoginRequiredMixin, View):
	success_url = reverse_lazy("billing_methods")

	def handle_form(self, request):
		stripe_id = request.POST.get("stripe_id", "")
		if not stripe_id.startswith(("card_", "src_")):
			# The Stripe ID of a card always starts with card_
			# For sources, it's always src_
			return False

		# `customer` is the StripeCustomer instance matching the current user
		customer = request.user.stripe_customer
		legacy_cards = customer.legacy_cards.all()
		sources = customer.sources_v3.all()

		try:
			# Get the payment method matching the stripe id, scoped to the customer
			card = legacy_cards.get(stripe_id=stripe_id)
			source = None
		except ObjectDoesNotExist:
			try:
				source = sources.get(stripe_id=stripe_id)
				card = None
			except ObjectDoesNotExist:
				return False

		if "delete" in request.POST:
			# Delete payment method
			if card:
				card.remove()
			elif source:
				source.detach()

			# If the default card is deleted, Stripe will automatically choose
			# a new default. A webhook will trigger to let us know that.
			# However, that data won't be ready in time for the response.
			# If we absolutely need to show the correct default, uncomment the
			# next two lines - but this will significantly slow down pageload.
			# stripe_customer = customer.api_retrieve()
			# Customer.sync_from_stripe_data(stripe_customer)

		elif "set_default" in request.POST:
			# Set the default payment method
			stripe_customer = customer.api_retrieve()
			stripe_customer.default_source = stripe_id
			try:
				stripe_customer.save()
			except InvalidRequestError:
				messages.error(self.request, _("Could not update default card."))
				# This may happen if the card does not exist (attempt to save
				# a default card that does not exist). Resync the customer's cards.
				customer._sync_cards()
			else:
				customer.__class__.sync_from_stripe_data(stripe_customer)

		return True

	def post(self, request):
		self.handle_form(request)
		return redirect(self.success_url)


class BasePaypalView(View):
	fail_url = reverse_lazy("premium")

	def fail(self, message):
		message = message + _(" Please contact us if you are seeing this in error.")
		messages.error(self.request, message)
		return redirect(self.fail_url)


class PaypalSuccessView(BasePaypalView):
	success_url = reverse_lazy("premium")

	def get_success_url(self):
		success_url = self.request.GET.get("next", "")
		if success_url and is_safe_url(success_url, allowed_hosts=None):
			return success_url
		return self.success_url

	def get(self, request):
		from djpaypal.models import PreparedBillingAgreement

		token = request.GET.get("token", "")
		if not token:
			return self.fail(_("Unable to complete subscription."))

		try:
			prepared_agreement = PreparedBillingAgreement.objects.get(id=token)
		except PreparedBillingAgreement.DoesNotExist:
			return self.fail(_("Invalid subscription token."))

		if prepared_agreement.user != self.request.user:
			return self.fail(_("You are not logged in as the correct user."))

		billing_agreement = prepared_agreement.execute()

		# At this time, we expect the billing agreement to be active
		# If that isn't the case, PayPal probably needs a moment to complete the payment
		# For now, let's just send a metric
		influx_metric(
			"hsreplaynet_paypal_agreement_state",
			{
				"count": "1",
				"id": billing_agreement.id
			},
			state=billing_agreement.state
		)

		# Null out the premium checkout timestamp so that we don't remind the user to
		# complete the checkout process.

		request.user.last_premium_checkout = None
		request.user.save()

		messages.success(self.request, _("You are now subscribed with PayPal!"))
		return redirect(self.get_success_url())


class PaypalCancelView(BasePaypalView):
	success_url = reverse_lazy("premium")

	def get_success_url(self):
		success_url = self.request.GET.get("next", "")
		if success_url and is_safe_url(success_url, allowed_hosts=None):
			return success_url
		return self.success_url

	def get(self, request):
		from djpaypal.models import PreparedBillingAgreement
		from djpaypal.exceptions import AgreementAlreadyExecuted
		token = request.GET.get("token", "")
		if token:
			try:
				prepared_agreement = PreparedBillingAgreement.objects.get(id=token)
			except PreparedBillingAgreement.DoesNotExist:
				return self.fail(_("Invalid token while cancelling payment."))

			try:
				prepared_agreement.cancel()
			except AgreementAlreadyExecuted:
				return self.fail(_("Payment has already completed and cannot be cancelled."))

			return redirect(self.get_success_url())

		return self.fail(_("Your payment was interrupted."))


class PaypalSubscribeView(LoginRequiredMixin, BasePaypalView):
	def post(self, request):
		from djpaypal.models import BillingPlan
		id = request.POST.get("plan", "")
		if not id:
			return self.fail(_("Could not determine your plan."))

		try:
			plan = BillingPlan.objects.get(id=id)
		except BillingPlan.DoesNotExist:
			return self.fail(_("Invalid Paypal plan."))

		# The start date of the plan is equal to a full period of the plan's
		# payment definition after now.
		# This is because the first period is paid as part of the "setup fee".
		# Why? Because in Paypal, the start date can't be "now", it always has
		# to be in the future. Putting it "in a few minutes" makes us prone to
		# race conditions where the API call can fail, or the user can cancel
		# their subscription before the first payment has arrived. On top of
		# this, without a setup fee, Paypal will tell the user that there will
		# be no initial payment, which is misleading.
		start_date = now() + plan.regular_payment_definition.frequency_delta
		override_merchant_preferences = {
			"setup_fee": plan.regular_payment_definition.amount.copy(),
		}

		prepared_agreement = plan.create_agreement(
			request.user, start_date=start_date,
			override_merchant_preferences=override_merchant_preferences
		)

		return redirect(prepared_agreement.approval_url)


class CheckoutNotificationView(LoginRequiredMixin, View):
	"""A handler for notifications that a user has started the premium checkout process."""

	@staticmethod
	def post(request):

		# Set the premium checkout timestamp so that we can identify users that didn't
		# complete the checkout process and remind them to finish.

		request.user.last_premium_checkout = timezone.now()
		request.user.save()

		return HttpResponse()
