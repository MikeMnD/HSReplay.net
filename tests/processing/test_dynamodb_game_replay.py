import os
from datetime import datetime

import pytest
from hearthstone import enums
from hslog.export import EntityTreeExporter
from hsreplay.document import HSReplayDocument
from tests.conftest import LOG_DATA_DIR

from hsreplaynet.games.processing import create_dynamodb_game_replay
from hsreplaynet.uploads.models import UploadEvent


@pytest.mark.django_db
def test_create_dynamodb_game_replay(auth_token):
	upload_event = UploadEvent(
		id="1",
		shortid="ccSgiGQaenVzXzwGYbaUTPGrv",
		token_uuid=auth_token.key,
	)

	meta = {
		"game_type": enums.BnetGameType.BGT_RANKED_STANDARD,
		"ladder_season": 42,
		"format": enums.FormatType.FT_STANDARD,
		"friendly_player": 1,
		"reconnecting": False,
		"scenario_id": 2,
		"start_time": datetime(
			year=2018, month=8, day=8, hour=19, minute=20, second=2, microsecond=606936
		),
		"end_time": datetime(year=2018, month=8, day=8, hour=19, minute=31, second=10),
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

	path = os.path.join(
		LOG_DATA_DIR,
		"hsreplaynet-tests",
		"replays",
		"whizbang_friendly.annotated.xml"
	)
	with open(path, "r") as f:
		replay = HSReplayDocument.from_xml_file(f)
	packet_tree = replay.to_packet_tree()[0]
	entity_tree = EntityTreeExporter(packet_tree).export().game
	replay_xml = "foo.xml"

	replay = create_dynamodb_game_replay(upload_event, meta, entity_tree, replay_xml)
	assert replay

	assert replay.user_id == auth_token.user.id
	assert replay.match_start == 1533756002606
	assert replay.match_end == 1533756670000

	assert replay.short_id == upload_event.shortid
	assert replay.digest is None

	assert replay.game_type == enums.BnetGameType.BGT_RANKED_STANDARD
	assert replay.format_type == enums.FormatType.FT_STANDARD

	assert replay.game_type_match_start == "2:1533756002606"

	assert replay.ladder_season == 42
	assert replay.brawl_season is None
	assert replay.scenario_id == 2
	assert replay.num_turns == 31

	assert replay.friendly_player_account_hilo == "144115193835963207_127487329"
	assert replay.friendly_player_battletag == "Masture#1176"
	assert replay.friendly_player_is_first
	assert replay.friendly_player_rank == 20
	assert replay.friendly_player_rank_stars == 30
	assert replay.friendly_player_legend_rank is None
	assert replay.friendly_player_wins is None
	assert replay.friendly_player_losses is None
	assert replay.friendly_player_class == enums.CardClass.WARLOCK
	assert replay.friendly_player_deck == \
		"AAECAf0GApfTAo+CAw4w9wTCCPYIm8sC980C8dAC8tAC9PcC0/gCqvkCt/0Cw/0C+v4CAA=="
	assert replay.friendly_player_blizzard_deck_id == 1337
	assert replay.friendly_player_cardback_id == 136
	assert replay.friendly_player_final_state == enums.PlayState.WON

	assert replay.opponent_account_hilo == "144115193835963207_50318740"
	assert replay.opponent_battletag == "GinyuGamer#1677"
	assert not replay.opponent_is_ai
	assert replay.opponent_rank == 19
	assert replay.opponent_legend_rank is None
	assert replay.opponent_class == enums.CardClass.PALADIN
	assert replay.opponent_hero == 671
	assert replay.opponent_revealed_deck == \
		"AAECAZ8FDYoGlgm5wQLjywKc4gKL5QKb8AKl9QKE/ALW/gKggAPMgQPeggMEiMcC/PwC4f4CkYADAA=="
	assert replay.opponent_predicted_deck is None
	assert replay.opponent_final_state == enums.PlayState.LOST

	assert replay.replay_xml == replay_xml
	assert not replay.disconnected
	assert not replay.reconnecting
	assert replay.hslog_version
	assert replay.visibility == auth_token.user.default_replay_visibility
	assert replay.views == 0
