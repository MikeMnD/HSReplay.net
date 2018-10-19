from datetime import datetime, timedelta

import fakeredis

from hsreplaynet.utils.redis import CappedDataFeed


def comparator(d1, d2):
	return (
		d1["field"] == d2["field"] and
		d1["field2"] == d2["field2"]
	)


def get_data(id):
	return {
		"id": id,
		"field": "value" + id,
		"field2": "value2" + id
	}


def test_comparator():
	redis = fakeredis.FakeStrictRedis()
	redis.flushall()

	data_1 = get_data("1")

	feed = CappedDataFeed(
		redis=redis,
		name="TEST_FEED",
		max_items=10,
		period=0,
		comparator=comparator
	)

	pushed = feed.push(data_1)
	assert pushed
	items = feed.get()
	assert len(items) == 1

	pushed = feed.push(data_1)
	assert not pushed
	items = feed.get()
	assert len(items) == 1


def test_period():
	redis = fakeredis.FakeStrictRedis()
	redis.flushall()

	data_1 = get_data("1")
	data_2 = get_data("2")

	feed = CappedDataFeed(
		redis=redis,
		name="TEST_FEED",
		max_items=10,
		period=1,
		comparator=comparator
	)

	pushed = feed.push(data_1)
	assert pushed
	items = feed.get()
	assert len(items) == 1
	assert items[0]["id"] == data_1["id"]

	pushed = feed.push(data_2)
	assert not pushed
	items = feed.get()
	assert len(items) == 1
	assert items[0]["id"] == data_1["id"]

	two_seconds_ago = int((datetime.utcnow() - timedelta(seconds=2)).timestamp())
	redis.set(feed.last_added_key, two_seconds_ago)

	pushed = feed.push(data_2)
	assert pushed
	items = feed.get()
	assert len(items) == 2
	assert items[0]["id"] == data_1["id"]
	assert items[1]["id"] == data_2["id"]


def test_fast_backfill():
	redis = fakeredis.FakeStrictRedis()
	redis.flushall()

	data_1 = get_data("1")
	data_2 = get_data("2")
	feed = CappedDataFeed(
		redis=redis,
		name="TEST_FEED",
		max_items=2,
		period=1,
		comparator=comparator,
		fast_backfill=True
	)

	pushed = feed.push(data_1)
	assert pushed
	items = feed.get()
	assert len(items) == 1
	assert items[0]["id"] == data_1["id"]

	pushed = feed.push(data_2)
	assert pushed
	items = feed.get()
	assert len(items) == 2
	assert items[1]["id"] == data_2["id"]

	pushed = feed.push(data_1)
	assert not pushed
	items = feed.get()
	assert len(items) == 2
	assert items[1]["id"] == data_2["id"]


def test_max_items():
	redis = fakeredis.FakeStrictRedis()
	redis.flushall()

	data_1 = get_data("1")
	data_2 = get_data("2")
	data_3 = get_data("3")

	feed = CappedDataFeed(
		redis=redis,
		name="TEST_FEED",
		max_items=2,
		period=0,
		comparator=comparator
	)

	pushed = feed.push(data_1)
	assert pushed
	items = feed.get()
	assert len(items) == 1
	assert items[0]["id"] == data_1["id"]

	key_1 = redis.lrange(feed.key, 0, 0)[0]
	assert redis.hgetall(key_1)

	pushed = feed.push(data_2)
	assert pushed
	items = feed.get()
	assert len(items) == 2
	assert items[0]["id"] == data_1["id"]
	assert items[1]["id"] == data_2["id"]

	pushed = feed.push(data_3)
	assert pushed
	items = feed.get()
	assert len(items) == 2
	assert items[0]["id"] == data_2["id"]
	assert items[1]["id"] == data_3["id"]

	assert len(redis.lrange(feed.key, 0, -1)) == 2
	assert not redis.hgetall(key_1)
