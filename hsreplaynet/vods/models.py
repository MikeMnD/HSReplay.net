import time

from django.conf import settings
from pynamodb.attributes import BooleanAttribute, NumberAttribute, UnicodeAttribute
from pynamodb.indexes import AllProjection, GlobalSecondaryIndex
from pynamodb.models import Model


class TwitchVodUserIdIndex(GlobalSecondaryIndex):
	"""A DynamoDB global secondary index to enable searching VODs by user id"""

	hsreplaynet_user_id = NumberAttribute(hash_key=True)
	combined_rank = UnicodeAttribute(range_key=True)

	class Meta:
		index_name = "by_hsreplaynet_user_id"
		projection = AllProjection()
		read_capacity_units = 2
		write_capacity_units = 20


class TwitchVodArchetypeIndex(GlobalSecondaryIndex):
	"""A DynamoDB global secondary index to enable searching VODs by archetype id"""

	friendly_player_archetype_id = NumberAttribute(hash_key=True)
	combined_rank = UnicodeAttribute(range_key=True)

	class Meta:
		index_name = "by_friendly_player_archetype_id"
		projection = AllProjection()
		read_capacity_units = 2
		write_capacity_units = 20


class TwitchVodDeckStringIndex(GlobalSecondaryIndex):
	"""A DynamoDB global secondary index to enable searching VODs by deck string"""

	friendly_player_canonical_deck_string = UnicodeAttribute(hash_key=True)
	combined_rank = UnicodeAttribute(range_key=True)

	class Meta:
		index_name = "by_friendly_player_deck_string"
		projection = AllProjection()
		read_capacity_units = 2
		write_capacity_units = 20


class TwitchVod(Model):
	"""A Twitch VOD link associated with a replay and mapped to a DynamoDB table"""

	twitch_channel_name = UnicodeAttribute(hash_key=True)  # The name of the Twitch channel
	friendly_player_name = UnicodeAttribute()  # The BattleTag for the friendly player
	hsreplaynet_user_id = NumberAttribute()  # The HSReplay.net user id of the uploader
	replay_shortid = UnicodeAttribute()  # The replay's shortid
	rank = NumberAttribute()  # The friendly player's rank

	# The friendly player's legend rank, when normal rank is 0, NULL otherwise

	legend_rank = NumberAttribute(null=True)

	# A synthetic key composing legend and normal rank to use as a DynamoDB range key

	combined_rank = UnicodeAttribute(range_key=True)

	won = BooleanAttribute()  # True if the friendly player won the game, else False
	went_first = BooleanAttribute()  # True if the friendly player went first, else False

	game_date = NumberAttribute()  # The epoch second timestamp of the match start
	game_length_seconds = NumberAttribute()  # The duration of the game in seconds

	format_type = UnicodeAttribute()  # The format of the game (as a FormatType enum name)
	game_type = UnicodeAttribute()  # The game type (as a BnetGameType enum name)

	# The full, canonicalized deck string for the friendly player
	friendly_player_canonical_deck_string = UnicodeAttribute()

	# The archetype id for the friendly player's deck, if available, else NULL
	friendly_player_archetype_id = NumberAttribute(null=True)

	# The player class of the opposing player (as a CardClass enum name)
	opposing_player_class = UnicodeAttribute()

	# The archetype id for the opposing player's deck, if available, else NULL
	opposing_player_archetype_id = NumberAttribute(null=True)

	url = UnicodeAttribute()  # The URL of the VOD on Twitch

	archetype_index = TwitchVodArchetypeIndex()
	deck_index = TwitchVodDeckStringIndex()
	user_id_index = TwitchVodUserIdIndex()

	# The TTL, in epoch seconds. DynamoDB must be told to use this attribute as the row TTL;
	# see https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html

	ttl = NumberAttribute()

	class Meta:
		table_name = settings.DYNAMODB_TABLES["twitch_vod"]["NAME"]
		host = settings.DYNAMODB_TABLES["twitch_vod"]["HOST"]
		if hasattr(settings, "AWS_CREDENTIALS"):
			aws_access_key_id = settings.AWS_CREDENTIALS["AWS_ACCESS_KEY_ID"]
			aws_secret_access_key = settings.AWS_CREDENTIALS["AWS_SECRET_ACCESS_KEY"]
		read_capacity_units = 2
		write_capacity_units = 5
		ttl_days = 14

	def __eq__(self, other):
		"""Overrides the default implementation"""

		if isinstance(other, TwitchVod):
			return self.__dict__ == other.__dict__
		return NotImplemented

	def __init__(self, *args, ttl=None, **kwargs):
		effective_ttl = ttl \
			if ttl else int(time.time() + TwitchVod.Meta.ttl_days * 24 * 60 * 60)
		super().__init__(*args, ttl=effective_ttl, **kwargs)
