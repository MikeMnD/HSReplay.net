import pytest
from hearthstone import enums


TEST_DRUID_ARCHETYPE = {
	"id": 1,
	"name": "Test Druid",
	"player_class": enums.CardClass.DRUID,
}

TEST_DRUID_ARCHETYPE_2 = {
	"id": 2,
	"name": "Test Druid 2",
	"player_class": enums.CardClass.DRUID,
}

TEST_DRUID_DECK_WRATH_1 = {
	"deck_id": "EKlKw4ILElCR1xS3abC65g",
	"deck_list": "[[43417,1],[42656,2],[45828,2],[43483,1],[381,2],[1124,2],[40991,1],[47063,2],[836,2],[503,1],[1029,2],[42759,2],[95,2],[43294,2],[64,2],[43288,2],[742,2]]", # flake8: noqa
	"archetype_id": 1,
	"win_rate": 56.67,
}

TEST_DRUID_DECK_WRATH_2 = {
	"deck_id": "dZbiSO2L9QQTwPj991OMz",
	"deck_list": "[[43417,1],[42656,2],[45828,2],[43483,2],[381,2],[1124,2],[45945,1],[47063,2],[836,1],[503,1],[1029,2],[42759,2],[95,2],[43294,2],[64,2],[43288,2],[742,2]]", # flake8: noqa
	"archetype_id": 2,
	"win_rate": 57.52,
}

TEST_DRUID_DECK_WRATH_3 = {
	"deck_id": "dZbIqtWpso2L9Qj991OMz",
	"deck_list": "[[43417,1],[42656,2],[45828,2],[43483,2],[381,2],[1124,2],[45945,1],[47063,2],[836,1],[503,1],[1029,2],[42759,2],[95,2],[43294,2],[64,2],[43288,2],[742,2]]", # flake8: noqa
	"archetype_id": 1,
	"win_rate": 55.52,
}

TEST_DRUID_DECK_NO_WRATH = {
	"deck_id": "qujK2o4dkGGEwNnXCNOU7g",
	"deck_list": "[[43417,1],[46032,1],[41418,2],[45945,2],[46551,2],[43025,2],[754,2],[46859,2],[41323,2],[41111,2],[734,2],[42759,2],[42442,2],[45265,2],[45340,1],[42395,2],[42818,1]]", # flake8: noqa
	"archetype_id": 205,
	"win_rate": 57.54,
}

TOKEN_DRUID_SUMMARY = {
	"name": {
		"enUS": "Token Druid"
	},
	"url": "https://hsreplay.net/archetypes/7/token-druid",
	"popularity": 3.37,
	"winrate": 53.6
}

DECK_DATA = {
	"DRUID": [
		TEST_DRUID_DECK_WRATH_1,
		TEST_DRUID_DECK_NO_WRATH,
		TEST_DRUID_DECK_WRATH_2,
		TEST_DRUID_DECK_WRATH_3
	],
}

WRATH_POPULARITY_DATA = {
	"dbf_id": 836,
	"popularity": 9.83,
	"winrate": 52.60,
}

RAVENCALLER_POPULARITY_DATA = {
	"dbf_id": 46661,
	"popularity": 0.23,
	"winrate": 44.51,
}

POPULARITY_DATA = [WRATH_POPULARITY_DATA, RAVENCALLER_POPULARITY_DATA]

@pytest.fixture(scope="function")
def archetypes_serializer_data():
	decks = dict(
		DRUID=[
			dict(
				archetype_id=1,
				win_rate=49.49,
				deck_id="abc",
				total_games=345
			), dict(
				archetype_id=1,
				win_rate=51.51,
				deck_id="abc2",
				total_games=234
			), dict(
				archetype_id=2,
				win_rate=52.52,
				deck_id="def",
				total_games=345
			)
		]
	)

	popularity = dict(
		DRUID=[
			dict(
				archetype_id=1,
				win_rate=50.50,
				pct_of_class=12.34,
				pct_of_total=4.56,
			), dict(
				archetype_id=2,
				win_rate=52.52,
				pct_of_class=23.45,
				pct_of_total=5.67,
			)
		]
	)

	matchups = {
		"1": {
			"2": dict(
				win_rate=50.50,
				total_games=123
			),
			"3": dict(
				win_rate=51.51,
				total_games=234
			),
			"4": dict(
				win_rate=52.52,
				total_games=345
			)
		},
		"2": {
			"3": dict(
				win_rate=50.50,
				total_games=123
			),
		}
	}
	return dict(
		decks=decks,
		popularity=popularity,
		matchups=matchups
	)
