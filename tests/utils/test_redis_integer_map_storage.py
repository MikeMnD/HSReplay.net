import json

import fakeredis

from hsreplaynet.utils.redis import RedisIntegerMapStorage


DECKS = [
	json.loads("[[308,2],[1182,2],[38725,1],[90,2],[1686,1],[395,2],[564,2],[315,2],[662,2],[906,2],[1004,2],[635,2],[216,2],[555,2],[608,2],[77,2]]"),  # NOQA
	json.loads("[[140,1],[38792,1],[38911,1],[2078,1],[232,1],[2029,2],[476,1],[584,2],[2726,2],[158,2],[1914,1],[1793,2],[1781,2],[1804,2],[679,1],[847,1],[2026,2],[1073,1],[2889,1],[2064,2],[943,1]]"),  # NOQA
	json.loads("[[38725,2],[825,1],[38857,1],[38859,2],[395,2],[38547,2],[38868,2],[315,2],[614,1],[662,2],[374,1],[38863,2],[906,1],[405,2],[1004,2],[38900,1],[555,2],[77,2]]")  # NOQA
]


def test_integer_map_storage():
	r = fakeredis.FakeStrictRedis()
	r.flushdb()

	storage = RedisIntegerMapStorage((r, r), "DECK")
	deck_ids = []

	for i, dbf_list in enumerate(DECKS):
		deck_id = i + 1
		deck_ids.append(deck_id)
		dbf_map = {dbf: c for dbf, c in dbf_list}
		storage.store(deck_id, dbf_map)
		retrieved_map = storage.retrieve(deck_id)
		assert list(sorted(retrieved_map.items())) == list(sorted(dbf_map.items()))

	for i, dbf_list in enumerate(DECKS):
		expected_deck_id = i + 1
		partial_map = {dbf: c for dbf, c in dbf_list[:-1]}
		assert int(storage.match(partial_map, *deck_ids)[0]) == expected_deck_id
