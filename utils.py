from datetime import datetime
from core import db
from models.user import User
from models.models import Donor, NgoEntity


def load_dummy_data():
    _ngo = NgoEntity(name='TEST NGO GOOD GUYS', \
                     url="test-ngo-good-guys", \
                     date_created=datetime.utcnow(),
                     description='best guys in the world',
                     website='http://www.goodguys1111.ro',
                     account='RO57NQFX2258814815293591',
                     cif='1234567'

                     )

    # noinspection PyArgumentList
    _admin = User(first_name='Adminescu',
                 last_name='Adminovici',
                 ngo=_ngo,
                 email='admin@example.com',
                 password='admin',
                 verified=True,
                 admin=True)
    # noinspection PyArgumentList
    _user = User(first_name='Utilizatorescu',
                 last_name='Userovici',
                 ngo=_ngo,
                 email='user1@example.com',
                 password='testuser',
                 verified=True,
                 admin=False)

    _donor = Donor(first_name='Donorescu', \
                   last_name='Donorovici', \
                   ngo=_ngo, \
                   date_created=datetime.utcnow())

    db.session.add(_ngo)

    db.session.add(_admin)

    db.session.add(_user)

    db.session.add(_donor)

    db.session.commit()


def obj2dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = str(getattr(row, column.name))
    return d
