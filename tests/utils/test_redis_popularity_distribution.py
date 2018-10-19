import time
from collections import defaultdict
from datetime import datetime, timedelta
from math import ceil

import fakeredis

from hsreplaynet.utils.redis import RedisPopularityDistribution


DECKS = [
	293400890,
	195890218,
	217541170,
	293400890,
	295568375,
	257802957,
	293400890,
	295563405,
	205220289,
	276545408,
	293400890,
	295570345,
	254488571,
	293400890,
	236780877,
	236633405,
	295536848,
	293400890,
	191000104,
	232775758,
	293400890,
	290743468,
	295234169,
	293400890,
	282172342,
]


def test_redis_popularity_distribution():
	r = fakeredis.FakeStrictRedis()
	distribution = RedisPopularityDistribution(r, "DECKS", namespace="test")

	actuals = defaultdict(int)
	for deck in DECKS:
		actuals[deck] += 1
		distribution.increment(deck)

	assert distribution.size() == 18
	assert distribution.observations() == len(DECKS)

	actual_most_popular = list(sorted(actuals.items(), key=lambda t: t[1], reverse=True))
	dist_most_popular = list(
		sorted(distribution.distribution().items(), key=lambda t: t[1], reverse=True)
	)
	actual_result = actual_most_popular[0][0]
	expected_result = int(dist_most_popular[0][0])

	assert actual_result == expected_result
	assert distribution.popularity(expected_result) == 32.0


def test_one_second_buckets():
	r = fakeredis.FakeStrictRedis()
	bucket_size = 1
	distribution = RedisPopularityDistribution(
		r,
		"DECKS",
		namespace="test",
		ttl=3600,
		bucket_size=bucket_size
	)
	current_ts = datetime.utcnow()
	td = timedelta(microseconds=current_ts.microsecond)
	t_0 = current_ts - td
	t_0_token = int(t_0.timestamp())

	start_token = distribution._to_start_token(t_0)
	assert start_token == t_0_token

	end_token = distribution._to_end_token(t_0)
	assert end_token == t_0_token

	end_token_from_start_token = distribution._convert_to_end_token(start_token)
	assert end_token_from_start_token == end_token

	next_token = distribution._next_token(start_token)
	assert next_token == (start_token + bucket_size)

	t_3 = t_0 + timedelta(seconds=3)
	buckets = distribution._generate_bucket_tokens_between(
		start_token,
		distribution._to_end_token(t_3)
	)
	for index, bucket in enumerate(buckets):
		assert bucket[0] == t_0_token + index
		assert bucket[1] == bucket[0] + (bucket_size - 1)


def test_bucket_sizes_and_ttls():
	r = fakeredis.FakeStrictRedis()
	distribution = RedisPopularityDistribution(
		r,
		"DECKS",
		ttl=5,
		namespace="test",
		bucket_size=1
	)

	# Create t_0 as 5 seconds in the past
	current_ts = datetime.utcnow()
	td = timedelta(seconds=5, microseconds=current_ts.microsecond)
	t_0 = current_ts - td

	def t_N(N):
		return t_0 + timedelta(seconds=N)

	distribution.increment("A", as_of=t_N(1))
	distribution.increment("B", as_of=t_N(2))
	distribution.increment("A", as_of=t_N(3))
	distribution.increment("A", as_of=t_N(4))

	# First assert the full distribution exists
	expected_distribution = {"A": 3.0, "B": 1.0}
	actual_distribution = distribution.distribution()
	assert expected_distribution == actual_distribution

	# Then assert accessing a partial distribution (t_2, t_3) within the full time range
	expected_distribution = {"A": 1.0, "B": 1.0}
	actual_distribution = distribution.distribution(start_ts=t_N(2), end_ts=t_N(3))
	assert expected_distribution == actual_distribution

	# Finally, assert that the first observation of "A" has aged out due to the TTL
	time.sleep(1)

	expected_distribution = {"A": 2.0, "B": 1}
	actual_distribution = distribution.distribution()
	assert expected_distribution == actual_distribution


def test_bucket_sizes():
	r = fakeredis.FakeStrictRedis()
	td = timedelta(days=1)
	current_ts = datetime.utcnow()
	yesterday_ts = current_ts - td

	# Test bucket sizes between 15 minutes and 6 hours in 15 minute increments
	for bucket_size in range(900, 21600, 900):
		dist = RedisPopularityDistribution(
			r, "DECKS", namespace="test", bucket_size=bucket_size
		)
		start_token = dist._to_start_token(current_ts)
		end_token = dist._to_end_token(current_ts)
		next_start_token = dist._next_token(start_token)
		assert end_token + 1 == next_start_token
		assert end_token - start_token == bucket_size - 1
		assert dist._convert_to_end_token(start_token) == end_token

		yesterday_start_token = dist._to_start_token(yesterday_ts)
		buckets = dist._generate_bucket_tokens_between(yesterday_start_token, end_token)

		# Assert the first bucket contains the start token
		first_bucket = buckets[0]
		assert first_bucket[0] == yesterday_start_token

		# Assert the last bucket matches the end token
		last_bucket = buckets[-1]
		assert last_bucket[1] == end_token

		# Assert the total number of buckets matches the expected number
		expected_num_buckets = ceil((end_token - yesterday_start_token) / bucket_size)
		assert len(buckets) == expected_num_buckets
