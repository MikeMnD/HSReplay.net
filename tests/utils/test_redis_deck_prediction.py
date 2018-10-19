import fakeredis
from hearthstone.enums import CardClass, FormatType

from hsreplaynet.utils.prediction import DeckPredictionTree


DOOMSAYER = 138
BLOODMAGE = 749
LOOTHOARDER = 251
FROSTNOVA = 587
FIREBALL = 315
BLIZZARD = 457
FROSTBOLT = 662


PLAY_SEQUENCES = {
	1: [
		LOOTHOARDER,
		LOOTHOARDER,
		FROSTBOLT,
		FROSTNOVA,
		DOOMSAYER,
	],
	2: [
		LOOTHOARDER,
		LOOTHOARDER,
		FIREBALL,
		FROSTNOVA,
		DOOMSAYER,
	]
}

DECK_1 = [LOOTHOARDER, LOOTHOARDER, FROSTBOLT, FROSTBOLT, FROSTNOVA, DOOMSAYER]
DECK_2 = [LOOTHOARDER, LOOTHOARDER, FIREBALL, FIREBALL, FROSTNOVA, DOOMSAYER]


def to_dbf_map(dbf_list):
	result = {}
	for dbf in dbf_list:
		if dbf not in result:
			result[dbf] = 0
		result[dbf] += 1
	return result


def test_prediction_tree():
	r = fakeredis.FakeStrictRedis()
	tree = DeckPredictionTree(
		CardClass.DRUID,
		FormatType.FT_STANDARD,
		r, r,
		max_depth=6,
		include_current_bucket=True
	)
	assert tree.tree_name == "DECK_PREDICTION_DRUID_FT_STANDARD"

	assert tree.lookup({}, []).predicted_deck_id is None

	tree.observe(1, to_dbf_map(DECK_1), PLAY_SEQUENCES[1])
	lookup_result_1 = tree.lookup(
		to_dbf_map(PLAY_SEQUENCES[1][:-1]),
		PLAY_SEQUENCES[1][:-1]
	).predicted_deck_id
	assert lookup_result_1 == 1

	tree.observe(2, to_dbf_map(DECK_2), PLAY_SEQUENCES[2])
	lookup_result_2 = tree.lookup(
		to_dbf_map(PLAY_SEQUENCES[2][:-1]),
		PLAY_SEQUENCES[2][:-1]
	)
	assert lookup_result_2.predicted_deck_id == 2
	# Assert proper path generation
	expected_path = ["ROOT"] + PLAY_SEQUENCES[2][:-1]
	assert lookup_result_2.path() == expected_path

	# Check that an unobserved play sequence returns None
	UNOBSERVED_PLAY_SEQUENCE = [
		BLIZZARD
	]
	lookup_result_5 = tree.lookup(
		to_dbf_map(UNOBSERVED_PLAY_SEQUENCE),
		UNOBSERVED_PLAY_SEQUENCE
	).predicted_deck_id
	assert lookup_result_5 is None
