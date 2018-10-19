from datetime import datetime, timedelta

import pytest
from hearthstone.enums import BnetRegion
from oauth2_provider.models import get_access_token_model, get_application_model
from oauthlib.common import generate_token

from hearthsim.identity.accounts.models import BlizzardAccount


@pytest.fixture
@pytest.mark.django_db
def collection_access(user):
	Application = get_application_model()
	application = Application.objects.create(
		name="Collection Test Access",
		allowed_scopes="collection:write",
	)

	AccessToken = get_access_token_model()
	token = AccessToken.objects.create(
		user=user,
		scope="collection:write",
		expires=datetime.now() + timedelta(days=365),
		token=generate_token(),
		application=application,
	)
	access_token = token.token

	blizzard_account = BlizzardAccount.objects.create(
		account_lo=123456789,
		account_hi=144115198130930503,
		region=BnetRegion.REGION_EU,
		user=user
	)
	account_lo = blizzard_account.account_lo
	region = blizzard_account.region

	return account_lo, region, access_token


@pytest.mark.django_db
def test_get_upload_url(client, mocker, collection_access):
	presign_url = mocker.patch("hsreplaynet.api.views.collections.S3.generate_presigned_url")
	presign_url.return_value = "https://example.com/put-collection-here"

	account_lo, region, access_token = collection_access

	url = "/api/v1/collection/upload_request/?account_lo=%d&region=%d" % (
		account_lo, int(region)
	)
	response = client.get(
		url, content_type="application/json",
		HTTP_AUTHORIZATION="Bearer %s" % access_token,
		HTTP_USER_AGENT="HDT/1.6.9.3642"
	)

	assert response.status_code == 200
	result = response.json()

	assert result["method"] == "PUT"
	assert result["account_lo"] == account_lo
	assert result["region"] == int(region)
	assert result["url"] == "https://example.com/put-collection-here"


@pytest.mark.django_db
def test_upload_user_agent_blacklist(client, mocker, settings, collection_access):
	presign_url = mocker.patch("hsreplaynet.api.views.collections.S3.generate_presigned_url")
	presign_url.return_value = "https://example.com/put-collection-here"

	settings.COLLECTION_UPLOAD_USER_AGENT_BLACKLIST = (
		"HDT/1.6.8.",
	)

	account_lo, region, access_token = collection_access

	url = "/api/v1/collection/upload_request/?account_lo=%d&region=%d" % (
		account_lo, int(region)
	)

	response = client.get(
		url, content_type="application/json",
		HTTP_AUTHORIZATION="Bearer %s" % access_token,
		HTTP_USER_AGENT="HDT/1.6.8.3639"
	)
	assert response.status_code == 403

	response = client.get(
		url, content_type="application/json",
		HTTP_AUTHORIZATION="Bearer %s" % access_token,
		HTTP_USER_AGENT="HDT/1.6.9.3642"
	)
	assert response.status_code == 200
