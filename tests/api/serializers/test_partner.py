import pytest
from django_hearthstone.cards.models import Card
from hearthstone import enums
from hearthstone.enums import CardClass
from tests.api.partner.fixtures import (
	DECK_DATA, POPULARITY_DATA, TEST_DRUID_ARCHETYPE,
	TEST_DRUID_ARCHETYPE_2, TEST_DRUID_DECK_WRATH_1,
	TEST_DRUID_DECK_WRATH_2, TOKEN_DRUID_SUMMARY, WRATH_POPULARITY_DATA
)

from hsreplaynet.api.partner.serializers import (
	ArchetypeDataSerializer, ArchetypeSerializer, CardDataDeckSerializer,
	CardDataSerializer, CardSerializer, ClassArchetypeStatsSerializer,
	ClassArchetypeSummarySerializer, ClassSerializer, InvalidCardException
)
from hsreplaynet.decks.models import Archetype


EXPLODED_DECK_DATA = {
	836: {
		1: TEST_DRUID_DECK_WRATH_1,
		2: TEST_DRUID_DECK_WRATH_2
	}
}

TOKEN_DRUID_ARCHETYPE = Archetype(id=7, name="Token Druid", player_class=2)

TOKEN_DRUID_STATS = {
	"archetype_id": 7,
	"pct_of_class": 21.6,
	"pct_of_total": 3.37,
	"total_games": 253279,
	"win_rate": 53.6
}

SPITEFUL_DRUID_ARCHETYPE = Archetype(id=205, name="Spiteful Druid", player_class=2)

SPITEFUL_DRUID_STATS = {
	"archetype_id": 205,
	"pct_of_class": 4.14,
	"pct_of_total": 0.65,
	"total_games": 48601,
	"win_rate": 52.33
}

SPITEFUL_DRUID_SUMMARY = {
	"name": {
		"enUS": "Spiteful Druid"
	},
	"url": "https://hsreplay.net/archetypes/205/spiteful-druid",
	"popularity": 0.65,
	"winrate": 52.33
}

QUEST_DRUID_ARCHETYPE = Archetype(id=150, name="Quest Druid", player_class=2)

QUEST_DRUID_STATS = {
	"archetype_id": 150,
	"pct_of_class": 1.52,
	"pct_of_total": 0.74,
	"total_games": 17849,
	"win_rate": 42.96
}

QUEST_DRUID_SUMMARY = {
	"name": {
		"enUS": "Quest Druid"
	},
	"url": "https://hsreplay.net/archetypes/150/quest-druid",
	"popularity": 0.74,
	"winrate": 42.96
}

MILL_DRUID_ARCHETYPE = Archetype(id=226, name="Mill Druid", player_class=2)

MILL_DRUID_STATS = {
	"archetype_id": 226,
	"pct_of_class": 3.29,
	"pct_of_total": 0.51,
	"total_games": 38579,
	"win_rate": 49.78
}

MILL_DRUID_SUMMARY = {
	"name": {
		"enUS": "Mill Druid"
	},
	"url": "https://hsreplay.net/archetypes/226/mill-druid",
	"popularity": 0.51,
	"winrate": 49.78
}

BIG_DRUID_ARCHETYPE = Archetype(id=148, name="Big Druid", player_class=2)

BIG_DRUID_STATS = {
	"archetype_id": 148,
	"pct_of_class": 12.71,
	"pct_of_total": 1.61,
	"total_games": 136787,
	"win_rate": 52.84,
}

BIG_DRUID_SUMMARY = {
	"name": {
		"enUS": "Big Druid"
	},
	"url": "https://hsreplay.net/archetypes/148/big-druid",
	"popularity": 1.61,
	"winrate": 52.84,
}

TAUNT_DRUID_ARCHETYPE = Archetype(id=149, name="Taunt Druid", player_class=2)

TAUNT_DRUID_STATS = {
	"archetype_id": 149,
	"pct_of_class": 22.11,
	"pct_of_total": 2.8,
	"total_games": 237963,
	"win_rate": 50.24,
}

TAUNT_DRUID_SUMMARY = {
	"name": {
		"enUS": "Taunt Druid"
	},
	"url": "https://hsreplay.net/archetypes/149/taunt-druid",
	"popularity": 2.8,
	"winrate": 50.24,
}

EXPECTED_TEST_DRUID_DECK_DATA_1 = {
	"name": {
		"enUS": TEST_DRUID_ARCHETYPE["name"]
	},
	"player_class": TEST_DRUID_ARCHETYPE["player_class"].name,
	"url": "https://hsreplay.net/decks/%s/" % TEST_DRUID_DECK_WRATH_1["deck_id"],
	"winrate": TEST_DRUID_DECK_WRATH_1["win_rate"],
}

EXPECTED_TEST_DRUID_DECK_DATA_2 = {
	"name": {
		"enUS": TEST_DRUID_ARCHETYPE_2["name"]
	},
	"player_class": TEST_DRUID_ARCHETYPE_2["player_class"].name,
	"url": "https://hsreplay.net/decks/%s/" % TEST_DRUID_DECK_WRATH_2["deck_id"],
	"winrate": TEST_DRUID_DECK_WRATH_2["win_rate"],
}

EXPECTED_WRATH_CARD_DATA = {
	"url": "https://hsreplay.net/cards/836/wrath#gameType=RANKED_STANDARD",
	"popularity": WRATH_POPULARITY_DATA["popularity"],
	"deck_winrate": WRATH_POPULARITY_DATA["winrate"],
	"top_decks": [EXPECTED_TEST_DRUID_DECK_DATA_2, EXPECTED_TEST_DRUID_DECK_DATA_1]
}

EXPECTED_WRATH_DATA = {
	"card_id": "EX1_154",
	"dbf_id": 836,
	"game_types": {
		"RANKED_STANDARD": EXPECTED_WRATH_CARD_DATA,
	}
}


@pytest.mark.django_db
@pytest.mark.usefixtures("archetypes_serializer_data")
def test_archetypes_serializer(archetypes_serializer_data):
	archetype = Archetype.objects.create(
		id=1,
		name="Archetype 1",
		player_class=enums.CardClass.DRUID,
	)

	mock_data = dict(
		game_type="RANKED_STANDARD",
		archetype=archetype,
	)
	context = dict(
		RANKED_STANDARD=dict(
			deck_data=archetypes_serializer_data["decks"],
			popularity_data=archetypes_serializer_data["popularity"],
			matchup_data=archetypes_serializer_data["matchups"]
		)
	)

	serializer = ArchetypeSerializer(instance=mock_data, context=context)
	data = serializer.data

	assert "id" in data
	assert data["id"] == 1

	assert "name" in data
	assert len(data["name"].keys()) == 1
	assert "enUS" in data["name"]
	assert data["name"]["enUS"] == "Archetype 1"

	assert "player_class" in data
	assert data["player_class"] == "DRUID"

	assert "url" in data
	assert data["url"] == "https://hsreplay.net/archetypes/1/archetype-1"

	assert "game_types" in data
	assert len(data["game_types"].keys()) == 1
	assert "RANKED_STANDARD" in data["game_types"]

	ranked_standard = data["game_types"]["RANKED_STANDARD"]
	assert "winrate" in ranked_standard
	assert ranked_standard["winrate"] == 50.50

	assert "class_popularity" in ranked_standard
	assert ranked_standard["class_popularity"] == 12.34

	assert "global_popularity" in ranked_standard
	assert ranked_standard["global_popularity"] == 4.56

	assert "matchups" in ranked_standard
	assert len(ranked_standard["matchups"]) == 3

	for i in range(0, 3):
		assert "id" in ranked_standard["matchups"][i]
		assert "winrate" in ranked_standard["matchups"][i]

	assert ranked_standard["matchups"][0]["id"] == 4
	assert ranked_standard["matchups"][0]["winrate"] == 52.52
	assert ranked_standard["matchups"][1]["id"] == 3
	assert ranked_standard["matchups"][1]["winrate"] == 51.51
	assert ranked_standard["matchups"][2]["id"] == 2
	assert ranked_standard["matchups"][2]["winrate"] == 50.50

	assert "most_popular_deck" in ranked_standard
	assert "url" in ranked_standard["most_popular_deck"]
	assert ranked_standard["most_popular_deck"]["url"] == "https://hsreplay.net/decks/abc/"
	assert "winrate" in ranked_standard["most_popular_deck"]
	assert ranked_standard["most_popular_deck"]["winrate"] == 49.49

	assert "best_performing_deck" in ranked_standard
	assert "url" in ranked_standard["best_performing_deck"]
	assert ranked_standard["best_performing_deck"]["url"] == "https://hsreplay.net/decks/abc2/"
	assert "winrate" in ranked_standard["best_performing_deck"]
	assert ranked_standard["best_performing_deck"]["winrate"] == 51.51


@pytest.mark.django_db
@pytest.mark.usefixtures("archetypes_serializer_data")
def test_archetypes_serializer_low_data(archetypes_serializer_data):
	archetype = Archetype.objects.create(
		id=2,
		name="Archetype 2",
		player_class=enums.CardClass.DRUID,
	)

	matchups = archetypes_serializer_data["matchups"]
	matchups["2"]["3"]["total_games"] = ArchetypeDataSerializer.MIN_GAMES_THRESHOLD - 1

	mock_data = dict(
		game_type="RANKED_STANDARD",
		archetype=archetype,
	)

	context = dict(
		RANKED_STANDARD=dict(
			deck_data=archetypes_serializer_data["decks"],
			popularity_data=archetypes_serializer_data["popularity"],
			matchup_data=matchups
		)
	)

	serializer = ArchetypeSerializer(instance=mock_data, context=context)
	data = serializer.data
	assert not data


class TestCardDataDeckSerializer(object):
	@pytest.mark.django_db
	def test_serialized_data(self):
		Archetype.objects.create(**TEST_DRUID_ARCHETYPE)
		serializer = CardDataDeckSerializer(TEST_DRUID_DECK_WRATH_1)
		assert serializer.data == EXPECTED_TEST_DRUID_DECK_DATA_1


class TestCardDataSerializer(object):
	@pytest.mark.django_db
	def test_serialized_data(self):
		Archetype.objects.create(**TEST_DRUID_ARCHETYPE)
		Archetype.objects.create(**TEST_DRUID_ARCHETYPE_2)
		data = {
			"game_type": "RANKED_STANDARD",
			"card": Card.objects.get(dbf_id=836)
		}
		context = {
			"deck_data": EXPLODED_DECK_DATA,
			"popularity_data": POPULARITY_DATA
		}
		serializer = CardDataSerializer(data, context=context)
		assert serializer.data == EXPECTED_WRATH_CARD_DATA

	@pytest.mark.django_db
	def test_missing_data(self):
		data = {
			"game_type": "RANKED_STANDARD",
			"card": Card.objects.get(dbf_id=836)
		}
		data = CardDataSerializer(data, context={
			"deck_data": {},
			"popularity_data": POPULARITY_DATA
		}).data
		with pytest.raises(InvalidCardException):
			data = CardDataSerializer(data, context={
				"deck_data": EXPLODED_DECK_DATA,
				"popularity_data": {}
			}).data

	@pytest.mark.django_db
	def test_missing_dbf_id(self):
		data = {
			"game_type": "RANKED_STANDARD",
			"card": Card.objects.get(dbf_id=1050)
		}
		with pytest.raises(InvalidCardException):
			data = CardDataSerializer(data, context={
				"deck_data": EXPLODED_DECK_DATA,
				"popularity_data": POPULARITY_DATA
			}).data


class TestCardSerializer(object):
	@pytest.mark.django_db
	def test_serialized_data(self):
		Archetype.objects.create(**TEST_DRUID_ARCHETYPE)
		Archetype.objects.create(**TEST_DRUID_ARCHETYPE_2)

		data = Card.objects.get(dbf_id=836)
		context = {
			"game_type_data": {
				"RANKED_STANDARD": {
					"deck_data": DECK_DATA,
					"popularity_data": POPULARITY_DATA,
				}
			}
		}

		serializer = CardSerializer(data, context=context)
		assert serializer.data == EXPECTED_WRATH_DATA


class TestClassArchetypeStatsSerializer(object):

	def test_serialized_data(self):
		serializer = ClassArchetypeStatsSerializer({
			"archetype": TOKEN_DRUID_ARCHETYPE,
			"stats": TOKEN_DRUID_STATS
		})
		assert serializer.data == TOKEN_DRUID_SUMMARY


class TestClassArchetypeSummarySerializer(object):

	def test_serialized_data(self):
		serializer = ClassArchetypeSummarySerializer({
			7: {
				"archetype": TOKEN_DRUID_ARCHETYPE,
				"stats": TOKEN_DRUID_STATS
			},
			205: {
				"archetype": SPITEFUL_DRUID_ARCHETYPE,
				"stats": SPITEFUL_DRUID_STATS
			},
			150: {
				"archetype": QUEST_DRUID_ARCHETYPE,
				"stats": QUEST_DRUID_STATS
			},
			226: {
				"archetype": MILL_DRUID_ARCHETYPE,
				"stats": MILL_DRUID_STATS
			},
			148: {
				"archetype": BIG_DRUID_ARCHETYPE,
				"stats": BIG_DRUID_STATS
			},
			149: {
				"archetype": TAUNT_DRUID_ARCHETYPE,
				"stats": TAUNT_DRUID_STATS
			}
		}, context={
			"game_type": "RANKED_STANDARD",
			"player_class": CardClass.DRUID
		})

		assert serializer.data == {
			"url": "https://hsreplay.net/decks/#playerClasses=DRUID",
			"top_archetypes": [
				TOKEN_DRUID_SUMMARY,
				BIG_DRUID_SUMMARY,
				SPITEFUL_DRUID_SUMMARY,
				TAUNT_DRUID_SUMMARY,
				MILL_DRUID_SUMMARY,
			],
			"popular_archetypes": [
				TOKEN_DRUID_SUMMARY,
				TAUNT_DRUID_SUMMARY,
				BIG_DRUID_SUMMARY,
				QUEST_DRUID_SUMMARY,
				SPITEFUL_DRUID_SUMMARY,
			]
		}


class TestClassSerializer(object):

	def test_serialized_data(self):
		serializer = ClassSerializer({
			"archetypes": [
				MILL_DRUID_ARCHETYPE,
				QUEST_DRUID_ARCHETYPE,
				SPITEFUL_DRUID_ARCHETYPE,
				TOKEN_DRUID_ARCHETYPE,
				BIG_DRUID_ARCHETYPE,
				TAUNT_DRUID_ARCHETYPE,
			],
			"player_class": CardClass.DRUID,
			"hero_cards": [
				Card(dbf_id=274, card_id="HERO_06", name="Malfurion Stormrage"),
				Card(dbf_id=50484, card_id="HERO_06a", name="Lunara")
			]
		}, context={
			"archetype_stats": {
				"RANKED_STANDARD": {
					"DRUID": [
						MILL_DRUID_STATS,
						QUEST_DRUID_STATS,
						SPITEFUL_DRUID_STATS,
						TOKEN_DRUID_STATS,
						BIG_DRUID_STATS,
						TAUNT_DRUID_STATS,
					]
				}
			}
		})

		assert serializer.data == {
			"id": "DRUID",
			"name": {
				"deDE": "Druide",
				"enUS": "Druid",
				"esES": "Druida",
				"esMX": "Druida",
				"frFR": "Druide",
				"itIT": "Druido",
				"jaJP": "ドルイド",
				"koKR": "드루이드",
				"plPL": "Druid",
				"ptBR": "Druida",
				"ruRU": "Друид",
				"thTH": "ดรูอิด",
				"zhCN": "德鲁伊",
				"zhTW": "德魯伊"
			},
			"heroes": [{
				"dbf_id": 274,
				"card_id": "HERO_06"
			}, {
				"dbf_id": 50484,
				"card_id": "HERO_06a"
			}],
			"game_types": {
				"RANKED_STANDARD": {
					"url": "https://hsreplay.net/decks/#playerClasses=DRUID",
					"top_archetypes": [
						TOKEN_DRUID_SUMMARY,
						BIG_DRUID_SUMMARY,
						SPITEFUL_DRUID_SUMMARY,
						TAUNT_DRUID_SUMMARY,
						MILL_DRUID_SUMMARY
					],
					"popular_archetypes": [
						TOKEN_DRUID_SUMMARY,
						TAUNT_DRUID_SUMMARY,
						BIG_DRUID_SUMMARY,
						QUEST_DRUID_SUMMARY,
						SPITEFUL_DRUID_SUMMARY
					]
				}
			}
		}
