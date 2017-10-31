import re
from collections import namedtuple
from datetime import date, datetime
from typing import Dict, List, Optional

import requests

api_url = "https://trello.com/1"
auth_params = {
    "key": "...",
    "token": "..."
}

inbox_list_id = "..."
to_do_list_id = "..."
in_progress_list_id = "..."
done_list_id = "..."
history_list_id = "..."


# working with api

def get_list_cards(list_id: str) -> Dict:
    return requests.get("%s/lists/%s/cards" % (api_url, list_id), auth_params).json()


def move_to_list(card_id: str, list_id: str) -> None:
    requests.put("%s/cards/%s" % (api_url, card_id), {"idList": list_id, **auth_params})


# other

tab_pattern = re.compile("\[(?P<dom>#|\d{1,2}(-d{1,2})?(,\d{1,2}(-d{1,2})?)*) "
                         "(?P<mon>#|\d{1,2}(-d{1,2})?(,\d{1,2}(-d{1,2})?)*) "
                         "(?P<dow>#|\d(-d)?(,\d(-d)?)*) "
                         "(?P<yr>#|\d{4}(-d{4})?(,\d{4}(-d{4})?)*)]")


def is_repetitive(card: Dict) -> bool:
    return re.search(tab_pattern, card["name"]) is not None


def is_repeating(card: Dict, d: date) -> bool:
    match = re.search(tab_pattern, card["name"])
    if not match:
        return False
    groups = match.groupdict()
    return all([any([contains(period, value) for period in periods])
                for periods, value
                in zip([parse_periods(psstr)
                        for psstr
                        in [groups["dom"], groups["mon"], groups["dow"], groups["yr"]]],
                       [d.day, d.month, d.weekday() + 1, d.year])])


def is_expiring(card: Dict, d: date) -> bool:
    due = card["due"]
    return datetime.strptime(due[0:10], "%Y-%m-%d").date() == d if due else False


# util

Period = namedtuple("Period", ["lower", "upper"])


def parse_period(pstr: str) -> Optional[Period]:
    if pstr == "#":
        return None
    parts = pstr.split("-")
    return Period(int(parts[0]), int(parts[-1]))


def parse_periods(psstr: str) -> List[Period]:
    return [parse_period(pstr) for pstr in psstr.split(",")]


def contains(period: Period, value: int) -> bool:
    return not period or period[0] <= value <= period[1]


# main

def main():
    today = date.today()
    # flush Done
    for card in get_list_cards(done_list_id):
        move_to_list(card["id"], inbox_list_id if is_repetitive(card) else history_list_id)
    # return In Progress to To Do
    for card in get_list_cards(in_progress_list_id):
        move_to_list(card["id"], to_do_list_id)
    # activate cards
    for card in get_list_cards(inbox_list_id):
        if is_expiring(card, today) or is_repeating(card, today):
            move_to_list(card["id"], to_do_list_id)


if __name__ == "__main__":
    main()
