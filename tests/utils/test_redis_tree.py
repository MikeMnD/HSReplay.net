import fakeredis

from hsreplaynet.utils.redis import RedisTree


def test_tree_node():
	r = fakeredis.FakeStrictRedis()
	tree = RedisTree(r, "DECK_PREDICTION")
	assert tree.key == "TREE:DECK_PREDICTION"

	root = tree.root
	assert root.depth == 0
	assert root.key == "TREE:DECK_PREDICTION:NODE:ROOT"

	child1 = root.get_child("CHILD1", create=True)
	assert child1 is not None
	assert child1.depth == 1
	assert child1.key == "TREE:DECK_PREDICTION:NODE:ROOT->CHILD1"
	assert r.sismember(root.children_key, "CHILD1")

	child2 = root.get_child("CHILD2", create=False)
	assert child2 is None
	assert not r.sismember(root.children_key, "CHILD2")

	favorite_card = "Ysera"
	child1.set("favorite_card", favorite_card)
	assert child1.get("favorite_card") == favorite_card
	assert r.hget(child1.key, "favorite_card").decode("utf8") == favorite_card

	child3 = child1.get_child("CHILD3", create=True)
	assert child3
	assert child3.key == "TREE:DECK_PREDICTION:NODE:ROOT->CHILD1->CHILD3"
