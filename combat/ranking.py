import math

from combat.app import db
from combat.conf import (
    RATE_CORRECTION_FACTOR,
    COUNT_CORRECTION_FACTOR,
    FUDICIAL_WIN_CREDIT,
    FUDICIAL_LOSE_CREDIT,
)


def rate_formula(d_rate, win):
    """
    Generate positive credit correction for decks that have low win rate,
    vice versa.
    """
    ratio = math.atan(d_rate * 60 + 1) * 4 / math.pi - 1
    if win:
        return ratio * FUDICIAL_WIN_CREDIT * RATE_CORRECTION_FACTOR
    return ratio * FUDICIAL_LOSE_CREDIT * RATE_CORRECTION_FACTOR


def count_formula(count, total):
    """Generate larger bonus for less used deck"""
    if count < 10:
        return 0
    addition = math.log(total) / math.log(count)
    fudicial = COUNT_CORRECTION_FACTOR * FUDICIAL_WIN_CREDIT
    if addition > fudicial:
        return fudicial
    return addition


def get_correction(deck, win):
    """Sum all corrections"""
    stat = db.decks.aggregate({"$group": {"_id": None,
                                          "total": {"$sum": "$count"},
                                          "total_win": {"$sum": "$win_count"},
                                          "total_lose": {"$sum": "$lose_count"}
                                          }})['result'][0]
    total = stat['total']
    total_win = stat['total_win']
    total_lose = stat['total_lose']
    if deck.count < 10 or total < 10:
        rate = 0
        total_rate = 0
        d_rate = 0
    else:
        rate = float(deck.win_count) / float(deck.count)
        total_rate = float(total_win) / float(total)
        d_rate = math.fabs(rate - total_rate)
    result = 0
    if rate > total_rate:
        result = result - \
            rate_formula(d_rate, win) + count_formula(deck.count, total)
    else:
        result = result - \
            rate_formula(d_rate, win) + count_formula(deck.count, total)
    return int(round(result))


def get_credit(deck, win):
    """Calculate actual credit of a duel"""
    if win:
        return int(FUDICIAL_WIN_CREDIT) + get_correction(deck, win)
    return -int(FUDICIAL_LOSE_CREDIT) + get_correction(deck, win)


get_winner_credit = lambda deck: get_credit(deck, True)
get_loser_credit = lambda deck: get_credit(deck, False)
