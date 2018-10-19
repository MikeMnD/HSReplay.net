from io import StringIO
from unittest.mock import Mock

import pytest
from django.core.management import call_command
from hearthstone import enums
from oauth2_provider.admin import AccessToken
from rest_framework import status
from tests.api.partner.fixtures import (
	DECK_DATA, POPULARITY_DATA, TEST_DRUID_ARCHETYPE,
	TEST_DRUID_ARCHETYPE_2, TOKEN_DRUID_SUMMARY
)

from hearthsim.identity.accounts.models import User
from hsreplaynet.api.partner.utils import QueryDataNotAvailableException
from hsreplaynet.api.partner.views import ClassesView
from hsreplaynet.decks.models import Archetype


@pytest.fixture
@pytest.mark.django_db
def user():
	return User.objects.create_user(
		username="bing", email="bing@example.com", is_fake=True, password="password"
	)


@pytest.fixture
def partner_token(user):
	out = StringIO()
	call_command(
		"grant_partner_access",
		user.username,
		noinput=True, stdout=out
	)

	token = AccessToken.objects.get(user=user)
	return str(token.token)


@pytest.mark.django_db
def test_archetypes_view_no_redshift_data(client, mocker, partner_token):
	def mock_get_query_data(self, query_name, game_type):
		raise QueryDataNotAvailableException()
	mocker.patch(
		"hsreplaynet.api.partner.views.ArchetypesView._get_query_data",
		new=mock_get_query_data
	)
	response = client.get(
		"/api/v1/partner-stats/archetypes/",
		HTTP_AUTHORIZATION="Bearer %s" % partner_token
	)
	assert response.status_code == status.HTTP_202_ACCEPTED


@pytest.mark.django_db
@pytest.mark.usefixtures("archetypes_serializer_data")
def test_archetypes_view_valid_data(
	archetypes_serializer_data, client, mocker, partner_token
):
	archetype = Archetype.objects.create(
		id=1,
		name="Archetype 1",
		player_class=enums.CardClass.DRUID,
	)

	def mock_get_query_data(self, query_name, game_type):
		if query_name == "list_decks_by_win_rate":
			return archetypes_serializer_data["decks"]
		elif query_name == "archetype_popularity_distribution_stats":
			return archetypes_serializer_data["popularity"]
		elif query_name == "head_to_head_archetype_matchups":
			return archetypes_serializer_data["matchups"]
		raise Exception()

	def mock_get_archetypes(self):
		return [archetype]
	mocker.patch(
		"hsreplaynet.api.partner.views.ArchetypesView._get_query_data",
		new=mock_get_query_data
	)
	mocker.patch(
		"hsreplaynet.api.partner.views.ArchetypesView._get_archetypes",
		new=mock_get_archetypes
	)
	response = client.get(
		"/api/v1/partner-stats/archetypes/",
		HTTP_AUTHORIZATION="Bearer %s" % partner_token
	)
	assert response.status_code == status.HTTP_200_OK
	assert response.data


def test_archetypes_view_not_authorized(client):
	response = client.get("/api/v1/partner-stats/archetypes/")
	assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestClassesView:
	view = ClassesView()

	@pytest.mark.django_db
	def test_list(self, client, mocker, partner_token):
		Archetype.objects.create(id=7, player_class=2, name="Token Druid")

		series_data = dict(
			(hsclass.name, [])
			for hsclass in enums.CardClass if hsclass.is_playable
		)
		series_data["DRUID"] = [{
			"archetype_id": 7,
			"pct_of_class": 21.6,
			"pct_of_total": 3.37,
			"total_games": 253279,
			"win_rate": 53.6
		}]

		mock_parameterized_query = Mock(
			result_available=True,
			response_payload=dict(
				series=dict(data=series_data)
			)
		)

		attrs = {
			"build_full_params.return_value": mock_parameterized_query
		}

		mocker.patch(
			"hsreplaynet.api.partner.views.get_redshift_query",
			lambda name: Mock(**attrs)
		)

		trigger_if_stale = mocker.patch("hsreplaynet.api.partner.views.trigger_if_stale")

		response = client.get(
			"/api/v1/partner-stats/classes/",
			content_type="application/json",
			HTTP_AUTHORIZATION="Bearer %s" % partner_token)

		assert response.status_code == 200
		trigger_if_stale.assert_called()

		response_list = response.json()
		response_classes = list(map(lambda x: x["id"], response_list))

		assert len(response_classes) == 9
		for hsclass in [
			enums.CardClass.DRUID,
			enums.CardClass.HUNTER,
			enums.CardClass.MAGE,
			enums.CardClass.PALADIN,
			enums.CardClass.PRIEST,
			enums.CardClass.ROGUE,
			enums.CardClass.SHAMAN,
			enums.CardClass.WARLOCK,
			enums.CardClass.WARRIOR,
		]:
			assert hsclass.name in response_classes

		for response_obj in response_list:
			assert response_obj["id"] in enums.CardClass.__members__
			for locale in response_obj["name"].keys():
				assert locale in enums.Locale.__members__

			ranked_standard = response_obj["game_types"]["RANKED_STANDARD"]

			assert isinstance(ranked_standard["url"], str)
			assert isinstance(ranked_standard["top_archetypes"], list)
			assert isinstance(ranked_standard["popular_archetypes"], list)

			if response_obj["id"] == "DRUID":
				assert ranked_standard["top_archetypes"] == [TOKEN_DRUID_SUMMARY]
				assert ranked_standard["popular_archetypes"] == [TOKEN_DRUID_SUMMARY]

	@pytest.mark.django_db
	def test_list_unauthorized(self, client):
		response = client.get("/api/v1/partner-stats/classes/", content_type="application/json")
		assert response.status_code == 401

		response = client.get(
			"/api/v1/partner-stats/classes/",
			content_type="application/json",
			HTTP_AUTHORIZATION="Bearer Not-A-Real-Access-Token")

		assert response.status_code == 401

	@pytest.mark.django_db
	def test_list_needs_refresh(self, client, mocker, partner_token):
		attrs = {
			"build_full_params.return_value": Mock(result_available=False)
		}

		mocker.patch(
			"hsreplaynet.api.partner.views.get_redshift_query",
			lambda name: Mock(**attrs)
		)

		trigger_if_stale = mocker.patch("hsreplaynet.api.partner.views.trigger_if_stale")

		response = client.get(
			"/api/v1/partner-stats/classes/",
			content_type="application/json",
			HTTP_AUTHORIZATION="Bearer %s" % partner_token)

		assert response.status_code == 202
		trigger_if_stale.assert_called()


@pytest.mark.django_db
def test_cards_view_no_redshift_data(client, mocker, partner_token):
	def mock_get_query_data(self, query_name, game_type):
		raise QueryDataNotAvailableException()
	mocker.patch(
		"hsreplaynet.api.partner.views.CardsView._get_query_data",
		new=mock_get_query_data
	)
	response = client.get(
		"/api/v1/partner-stats/cards/",
		HTTP_AUTHORIZATION="Bearer %s" % partner_token
	)
	assert response.status_code == status.HTTP_202_ACCEPTED


@pytest.mark.django_db
def test_cards_view_valid_data(client, mocker, partner_token):
	Archetype.objects.create(**TEST_DRUID_ARCHETYPE)
	Archetype.objects.create(**TEST_DRUID_ARCHETYPE_2)

	def mock_get_query_data(self, query_name, game_type):
		if query_name == "list_decks_by_win_rate":
			return DECK_DATA
		elif query_name == "card_included_popularity_report":
			return {"ALL": POPULARITY_DATA}
		raise Exception()

	mocker.patch(
		"hsreplaynet.api.partner.views.CardsView._get_query_data",
		new=mock_get_query_data
	)
	response = client.get(
		"/api/v1/partner-stats/cards/",
		HTTP_AUTHORIZATION="Bearer %s" % partner_token
	)
	assert response.status_code == status.HTTP_200_OK
	assert response.data


def test_cards_view_not_authorized(client):
	response = client.get("/api/v1/partner-stats/cards/")
	assert response.status_code == status.HTTP_401_UNAUTHORIZED
