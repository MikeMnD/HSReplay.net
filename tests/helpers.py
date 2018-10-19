from django_hearthstone.cards.models import Card
from hearthstone import enums
from hearthstone.deckstrings import parse_deckstring
from shortuuid import ShortUUID

from hearthsim.identity.accounts.models import BlizzardAccount
from hsreplaynet.decks.models import Archetype, Deck
from hsreplaynet.games.models import GameReplay, GlobalGamePlayer
from hsreplaynet.utils import card_db


def create_deck_from_deckstring(deckstring, archetype_id=None):
	db = card_db()
	cards, heroes, format = parse_deckstring(deckstring)

	card_ids = []
	for card in cards:
		for _ in range(card[1]):
			card_ids.append(db[card[0]].id)

	deck_list, _ = Deck.objects.get_or_create_from_id_list(
		card_ids,
		hero_id=heroes[0],
		game_type=enums.BnetGameType.BGT_RANKED_STANDARD
	)

	if archetype_id:
		archetype = Archetype(id=archetype_id)
		archetype.save()

		deck_list.archetype = archetype
		deck_list.save()

	return deck_list


def create_player(
	name,
	id,
	deck,
	game,
	rank=25,
	legend_rank=None,
	is_ai=False,
	is_first=True
):
	blizzard_account = BlizzardAccount(
		account_hi=id,
		account_lo=id,
		region=enums.BnetRegion.REGION_US
	)
	blizzard_account.save()

	player = GlobalGamePlayer(
		name=name,
		player_id=id,
		deck_list=deck,
		game=game,
		hero=Card.objects.get(card_id=deck.hero or "HERO_01"),
		is_ai=is_ai,
		is_first=is_first,
		pegasus_account=blizzard_account,
		rank=rank
	)

	if legend_rank:
		player.legend_rank = legend_rank

	player.save()
	return player


def create_replay(user, game, friendly_player_id=1):
	replay = GameReplay(
		user=user,
		global_game=game,
		friendly_player_id=friendly_player_id,
		shortid=ShortUUID().random()
	)
	replay.save()

	return replay
