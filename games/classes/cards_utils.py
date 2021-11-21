import random
cards_prefix = {
    '2', '3', '4', '5', '6', '7', '8',
    '9', '0', 'J', 'Q', 'K', 'A'
}
cards_symbols = {'C', 'D', 'H', 'S'}


def get_cards_deck():
    cards = []
    for prefix in cards_prefix:
        for symbol in cards_symbols:
            cards.append(prefix + symbol)
    return cards


def get_random_card(card_deck):
    return random.choice(card_deck)


def get_random_hand(card_deck, number_of_cards):
    cards = []
    for _ in range(number_of_cards):
        card = get_random_card(card_deck)
        card_deck.remove(card)
        cards.append(card)
    return card_deck, cards
