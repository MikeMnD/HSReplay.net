"""
Miscellaneous middleware objects
"""

from ipaddress import ip_address

from django.conf import settings
from django.templatetags.static import static
from django.utils import timezone, translation
from djpaypal.models import BillingAgreement

from .html import HTMLHead
from .i18n import lang_to_opengraph


class DoNotTrackMiddleware:
	HEADER = "HTTP_DNT"

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if self.HEADER in request.META:
			request.dnt = request.META[self.HEADER] == "1"
		else:
			request.dnt = None

		response = self.get_response(request)

		if self.HEADER in request.META:
			response["DNT"] = request.META[self.HEADER]

		return response


class MetaTagsMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		request.head = HTMLHead(request)
		thumbnail = static("images/hsreplay-thumbnail.png")
		request.head.add_meta(
			{"name": "viewport", "content": "width=device-width, initial-scale=1"},
		)

		request.head.opengraph["og:type"] = "website"
		request.head.opengraph["og:site_name"] = "HSReplay.net"
		request.head.opengraph["og:locale"] = lang_to_opengraph(translation.get_language())
		request.head.opengraph["og:image"] = request.build_absolute_uri(thumbnail)
		request.head.opengraph["og:image:width"] = 400
		request.head.opengraph["og:image:height"] = 400

		twitter_handle = getattr(settings, "HSREPLAY_TWITTER_HANDLE", "")
		if twitter_handle:
			request.head.add_meta({"name": "twitter:site", "content": "@" + twitter_handle})

		facebook_app_id = getattr(settings, "HSREPLAY_FACEBOOK_APP_ID", "")
		if facebook_app_id:
			# This is intentionally "property"
			request.head.opengraph["fb:app_id"] = facebook_app_id

		response = self.get_response(request)
		return response


class UserLocaleMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.user.is_authenticated:
			if request.user.locale:
				translation.activate(request.user.locale)
				request.LANGUAGE_CODE = translation.get_language()

		response = self.get_response(request)

		return response


class HostLanguageMiddleware:
	PARAM = "hl"

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.method == "GET" and self.PARAM in request.GET:
			request.host_language = request.GET.get(self.PARAM)
			translation.activate(request.host_language)
			request.LANGUAGE_CODE = translation.get_language()

		response = self.get_response(request)
		return response


class SetRemoteAddrFromForwardedFor:
	"""
	Middleware that sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, if the
	latter is set and the IP is in a set of internal IPs.

	Note that this does NOT validate HTTP_X_FORWARDED_FOR. If you're not behind
	a reverse proxy that sets HTTP_X_FORWARDED_FOR automatically, do not use
	this middleware. Anybody can spoof the value of HTTP_X_FORWARDED_FOR, and
	because this sets REMOTE_ADDR based on HTTP_X_FORWARDED_FOR, that means
	anybody can "fake" their IP address. Only use this when you can absolutely
	trust the value of HTTP_X_FORWARDED_FOR.

	The code is from Django 1.0, but removed as unfit for general use.
	"""

	HEADERS = [
		"HTTP_CF_CONNECTING_IP",
		"HTTP_X_FORWARDED_FOR",
	]

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		# Check the original IP; only proceed if it's not a "real" IP
		ip = ip_address(request.META.get("REMOTE_ADDR", "127.0.0.1"))

		if ip.is_private:
			for header in self.HEADERS:
				if header in request.META:
					real_ip = request.META[header].split(",")[0].strip()
					request.META["REMOTE_ADDR"] = real_ip
					break

		response = self.get_response(request)
		return response


class UserActivityMiddleware:
	"""Middleware for updating last access time for authenticated users."""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.user.is_authenticated:
			request.user.last_site_activity = timezone.now()
			request.user.save()

		response = self.get_response(request)
		return response


class PayPalSyncMiddleware:
	"""Middleware for updating PayPal subscriptions that are stuck in pending state"""

	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if request.user and request.user.is_authenticated:
			for agreement in BillingAgreement.objects.filter(user=request.user, state="Pending"):
				BillingAgreement.find_and_sync(agreement.id)

		response = self.get_response(request)
		return response
