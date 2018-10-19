from datetime import timedelta
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.utils import timezone
from oauth2_provider.admin import AccessToken
from oauth2_provider.models import get_application_model

from hsreplaynet.api.partner.permissions import FEATURE
from hsreplaynet.features.utils import feature_enabled_for_user


def test_grant_partner_access(user):
	out = StringIO()
	call_command(
		"grant_partner_access",
		user.username,
		noinput=True, stdout=out
	)

	token = AccessToken.objects.get(user=user)

	assert token
	assert token.token
	assert token.user == user, \
		"The token is not owned by the specified user"
	assert token.application, \
		"The token is not associated with an app"
	assert token.application.user == user, \
		"The associated app is not associated with the specified user"
	assert token.expires > timezone.now() + timedelta(days=365 * 50), \
		"The token is not valid for at least 50 years"
	assert not token.is_expired(), \
		"The token has expired"
	assert token.is_valid(scopes=["stats.partner:read"]), \
		"The token is invalid"
	assert token.token in out.getvalue(), \
		"The token was not printed as output"
	assert feature_enabled_for_user(FEATURE, user), \
		"The user does not have access to the feature"


def test_grant_partner_access_wrong_scope(user):
	Application = get_application_model()
	app = Application(
		name="Partner API Application",
		user=user,
		allowed_scopes="some.scope:read",
		legacy_key="legacy_key"
	)
	app.save()

	out = StringIO()
	with pytest.raises(
		CommandError,
		message="The command should raise when the application's scope does not match"
	):
		call_command(
			"grant_partner_access",
			user.username, reuse_application=app.id,
			noinput=True, stdout=out
		)


def test_grant_partner_access_wrong_user(user):
	User = get_user_model()
	wrong_user = User.objects.create_user(
		username="wrong_user",
		email="wrong@example.com",
		is_fake=True,
		password="password"
	)

	Application = get_application_model()
	app = Application(
		name="Partner API Application",
		user=wrong_user,
		allowed_scopes="some.scope:read",
		legacy_key="legacy_key"
	)
	app.save()

	out = StringIO()
	with pytest.raises(
		CommandError,
		message="The command should raise when the application's user does not match"
	):
		call_command(
			"grant_partner_access",
			user.username, reuse_application=app.id,
			noinput=True, stdout=out
		)
