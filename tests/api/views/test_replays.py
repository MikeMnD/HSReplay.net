import json
import os

import pytest
from hearthstone import enums
from hslog.export import EntityTreeExporter
from hsreplay.document import HSReplayDocument
from rest_framework import status
from tests.conftest import LOG_DATA_DIR
from tests.test_raw_upload_processing import (  # noqa: F401
	game_replay_dynamodb_table, multi_db
)

from hearthsim.identity.accounts.models import Visibility
from hsreplaynet.games.processing import create_dynamodb_game_replay
from hsreplaynet.uploads.models import UploadEvent


@pytest.fixture
def public_replay_api(mocker):
	mocker.patch.multiple(
		"hsreplaynet.api.views.replays.GameReplayListView",
		authentication_classes=(),
		permission_classes=(),
	)


def _parse_streaming_json(iterator):
	return json.loads(b"".join(iterator))


@pytest.mark.usefixtures("public_replay_api")
def test_replays_api_missing_user_id(client):
	response = client.get("/api/v1/replays/")
	assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.usefixtures("game_replay_dynamodb_table", "public_replay_api")
def test_replays_api_wrong_user_id(client):
	response = client.get("/api/v1/replays/?user_id=1")
	assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@pytest.mark.usefixtures("game_replay_dynamodb_table", "public_replay_api")
def test_replays_api_empty(client, user):
	response = client.get("/api/v1/replays/?user_id=%d" % user.id)
	assert response.status_code == status.HTTP_200_OK
	assert _parse_streaming_json(response.streaming_content) == []


@pytest.mark.django_db
@pytest.mark.usefixtures("multi_db", "game_replay_dynamodb_table", "public_replay_api")
def test_replays_api(auth_token, client, mocker):
	mocker.patch("hsreplaynet.api.serializers.replays.classify_deck", return_value=1)
	upload_event = UploadEvent(
		id="1",
		shortid="ccSgiGQaenVzXzwGYbaUTPGrv",
		token_uuid=auth_token.key,
	)

	path = os.path.join(
		LOG_DATA_DIR,
		"hsreplaynet-tests",
		"replays",
		"whizbang_friendly.annotated.xml"
	)
	with open(path, "r") as f:
		replay = HSReplayDocument.from_xml_file(f)
	packet_tree = replay.to_packet_tree()[0]

	meta = {
		"game_type": enums.BnetGameType.BGT_RANKED_STANDARD,
		"ladder_season": 42,
		"format": enums.FormatType.FT_STANDARD,
		"friendly_player": 1,
		"reconnecting": False,
		"scenario_id": 2,
		"start_time": packet_tree.start_time,
		"end_time": packet_tree.end_time,
		"player1": {
			"rank": 20,
			"stars": 30,
			"deck": [
				"BOT_447",
				"BOT_447",
				"EX1_319",
				"EX1_319",
				"LOOT_014",
				"LOOT_014",
				"BOT_263",
				"BOT_263",
				"BOT_568",
				"CS2_065",
				"CS2_065",
				"EX1_596",
				"EX1_596",
				"BOT_443",
				"BOT_443",
				"LOOT_013",
				"LOOT_013",
				"BOT_224",
				"BOT_224",
				"BOT_226",
				"BOT_226",
				"ICC_466",
				"ICC_466",
				"ICC_075",
				"ICC_075",
				"EX1_310",
				"EX1_310",
				"BOT_521",
				"BOT_521",
				"ICC_831",
			],
			"deck_id": 1337,
			"cardback": 136,
		},
		"player2": {
			"rank": 19,
			"cardback": 138,
		},
	}

	entity_tree = EntityTreeExporter(packet_tree).export().game
	replay_xml = "foo.xml"

	replay = create_dynamodb_game_replay(upload_event, meta, entity_tree, replay_xml)
	replay.save()

	user_id = auth_token.user.id

	response = client.get("/api/v1/replays/?user_id=%d" % (user_id))
	assert response.status_code == status.HTTP_200_OK
	payload = _parse_streaming_json(response.streaming_content)[0]

	assert payload["user_id"] == user_id
	assert payload["match_start"] == "2018-08-08T21:20:02.610000Z"
	assert payload["match_end"] == "2018-08-08T21:31:10.236000Z"
	assert payload["shortid"] == "ccSgiGQaenVzXzwGYbaUTPGrv"
	assert payload["game_type"] == enums.BnetGameType.BGT_RANKED_STANDARD
	assert payload["format_type"] == enums.FormatType.FT_STANDARD

	assert payload["friendly_player_account_hi"] == "144115193835963207"
	assert payload["friendly_player_account_lo"] == "127487329"
	assert payload["friendly_player_battletag"] == "Masture#1176"
	assert payload["friendly_player_rank"] == 20

	assert payload["friendly_player_archetype_id"] == 1

	assert payload["opponent_account_hi"] == "144115193835963207"
	assert payload["opponent_account_lo"] == "50318740"
	assert payload["opponent_battletag"] == "GinyuGamer#1677"
	assert payload["opponent_rank"] == 19

	assert payload["opponent_archetype_id"] is None

	assert payload["replay_xml"] == "foo.xml"
	assert payload["disconnected"] is False
	assert payload["reconnecting"] is False
	assert payload["visibility"] == Visibility.Public
	assert payload["views"] == 0
