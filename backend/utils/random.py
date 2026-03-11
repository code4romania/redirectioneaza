import random


def random_25p():
    """
    25% chance of True
    """
    return random.choice((True, False, False, False))


def random_33p():
    """
    33% chance of True
    """
    return random.choice((True, False, False))


def random_50p():
    """
    50% chance of True
    """
    return random.choice((True, False))


def random_66p():
    """
    66% chance of True
    """
    return random.choice((True, True, False))


def random_75p():
    """
    75% chance of True
    """
    return random.choice((True, True, True, False))
