"""
This file contains helper functions.
"""


def obj2dict(row):
    """
    Marshalling function - transforms object into a dictionary
    :param row: SQLAlchemy object
    :return: dictionary
    """
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d
