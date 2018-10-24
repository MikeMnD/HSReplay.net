from django.contrib.auth import get_user_model
from rest_framework import fields, serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from hsreplaynet.api.fields import TimestampField
from hsreplaynet.api.permissions import UserHasFeature
from hsreplaynet.decks.models import Deck
from hsreplaynet.vods.models import TwitchVod


class VodRequestSerializer(serializers.Serializer):
	deck_id = fields.CharField(required=False)
	user_id = fields.IntegerField(required=False)

	# In order to support archetypes here you add archetype_id with required=False
	# add a it to fields in validate()

	def validate_deck_id(self, value):
		if not value:
			return None

		try:
			if value.isdigit():
				deck = Deck.objects.get(id=value)
			else:
				deck = Deck.objects.get_by_shortid(value)
		except Deck.DoesNotExist:
			raise serializers.ValidationError("Invalid deck ID")

		if not deck.is_full_deck:
			raise serializers.ValidationError("Invalid deck ID")

		return deck.id

	def validate_user_id(self, value):
		if not value:
			return None

		User = get_user_model()

		try:
			user = User.objects.get(pk=value)
		except User.DoesNotExist:
			raise serializers.ValidationError("Invalid user ID")

		return user.id

	def validate(self, data):
		fields = ["user_id", "deck_id"]
		field_data = [data.get(field, None) for field in fields]
		valid_fields = sum(1 for field in field_data if field)

		if valid_fields < 1:
			raise serializers.ValidationError(
				"%s must be specified." % " or ".join(fields)
			)

		if valid_fields > 1:
			raise serializers.ValidationError(
				"Too many identifiers. Only %s must be specified." % " or ".join(fields)
			)
		return data


class VodSerializer(serializers.Serializer):
	"""A serializer to extract from a TwitchVod model instance"""
	channel_name = fields.CharField(source="twitch_channel_name")
	url = fields.URLField()
	game_date = TimestampField(precision=1)
	game_type = fields.CharField()
	rank = fields.IntegerField()
	legend_rank = fields.IntegerField(allow_null=True)
	friendly_player_archetype_id = fields.IntegerField(allow_null=True)
	opposing_player_class = fields.CharField()
	opposing_player_archetype_id = fields.IntegerField(allow_null=True)
	won = fields.BooleanField()
	went_first = fields.BooleanField()
	game_length_seconds = fields.IntegerField()


class VodListView(APIView):
	"""Query for Twitch VODs by deck id or user id."""
	serializer_class = VodRequestSerializer
	authentication_classes = (SessionAuthentication, )
	permission_classes = (IsAuthenticated, UserHasFeature("twitch-vods"))

	def get(self, request, **kwargs):
		input = self.serializer_class(data=request.GET)
		input.is_valid(raise_exception=True)
		vods = []

		if "deck_id" in input.validated_data:
			deck = Deck.objects.get(id=input.validated_data["deck_id"])
			deckstring = deck.deckstring

			for vod in TwitchVod.deck_index.query(deckstring):
				serializer = VodSerializer(instance=vod)
				vods.append(serializer.data)
		elif "user_id" in input.validated_data:
			User = get_user_model()
			user = User.objects.get(pk=input.validated_data["user_id"])

			for vod in TwitchVod.user_id_index.query(user.id):
				serializer = VodSerializer(instance=vod)
				vods.append(serializer.data)

		return Response(vods)
