from datetime import date, datetime

import requests

api_url = "https://trello.com/1"
auth_params = {
    "key": "...",
    "token": "..."
}

inbox_list_id = "..."
to_do_list_id = "..."
done_list_id = "..."
history_list_id = "..."


# working with api

def get_list_cards(list_id):
    return requests.get("%s/lists/%s/cards" % (api_url, list_id), auth_params).json()


def move_to_list(card_id, list_id):
    requests.put("%s/cards/%s" % (api_url, card_id), {"idList": list_id, **auth_params})


# other

def is_repetitive(card):
    first_line = [*card["desc"].split("\n", 1), None][0]
    return first_line.startswith("repeat ")


def is_repeating(card, d):
    first_line = [*card["desc"].split("\n", 1), None][0]
    if not first_line.startswith("repeat "):
        return False
    tab = first_line[7:]
    return is_date_match(tab, d)


def is_expiring(card, d):
    due = card["due"]
    return datetime.strptime(due[0:10], "%Y-%m-%d").date() == d if due else False


# util

def parse_period(pstr: str):
    if pstr == "#":
        return None
    parts = pstr.split("-")
    return int(parts[0]), int(parts[-1])


def parse_periods(psstr: str):
    return [parse_period(pstr) for pstr in psstr.split(",")]


def contains(period, value):
    return not period or period[0] <= value <= period[1]


def is_date_match(tab: str, d):
    return all([any([contains(period, value) for period in periods])
                for periods, value
                in zip([parse_periods(i) for i in tab.split(" ")],
                       [d.day, d.month, d.weekday() + 1, d.year])])


# main

def main():
    today = date.today()
    # flush Done
    for card in get_list_cards(done_list_id):
        move_to_list(card["id"], inbox_list_id if is_repetitive(card) else history_list_id)
    # activate cards
    for card in get_list_cards(inbox_list_id):
        if is_expiring(card, today) or is_repeating(card, today):
            move_to_list(card["id"], to_do_list_id)


if __name__ == "__main__":
    main()
