from datetime import datetime
from core import db
from models.user import User
from models.models import Donor, NgoEntity


def load_dummy_data():

    _ngo = NgoEntity(name='TEST NGO GOOD GUYS',\
                     date_created = datetime.utcnow() )
    
    _user = User(first_name = 'Utilizatorescu',\
                 last_name = 'Userovici',\
                 ngo = _ngo.id,\
                 email = 'user1@example.com',\
                 password='testuser',\
                 verified=True)

    _donor = Donor(first_name = 'Donorescu',\
                   last_name = 'Donorovici',\
                   ngo=_ngo.id,\
                   date_created = datetime.utcnow())

    db.session.merge(_ngo)

    db.session.merge(_user)

    db.session.merge(_donor)

    db.session.commit()