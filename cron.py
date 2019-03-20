from logging import info

from core import db
from models.handlers import Handler
from models.models import NgoEntity


# TODO Incorporate this in manage.py
class NgoRemoveForms(Handler):

    def get(self):
        # get all the ngos
        ngos = NgoEntity.query.all()

        info(f'Removing form_url from {len(ngos)} ngos.')

        for ngo in ngos:
            ngo.form_url = None
            db.session.add(ngo)

        db.session.commit()
