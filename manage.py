"""
Manager console for the application. Can be called using `python manage.py`.
Available functionality:
    - database init, drop, load dummy data
    - Flask-Migrate commands for migrations
"""

from datetime import datetime

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, prompt_bool

from redirectioneaza import app, db
from redirectioneaza.models import Donor, NgoEntity, User

manager = Manager(app)
migrate = Migrate(app, db)

# Binds Flask-Migrate commands to management console. See more https://flask-migrate.readthedocs.io/en/latest/
manager.add_command('migrations', MigrateCommand)


def load_dummy_data():
    """
    Inserts dummy data entities for development purposes.
    """
    _ngo = NgoEntity(name='TEST NGO GOOD GUYS',
                     url="test-ngo-good-guys",
                     date_created=datetime.utcnow(),
                     description='best guys in the world',
                     website='http://www.goodguys1111.ro',
                     account='RO57NQFX2258814815293591',
                     cif='1234567',
                     address='Str. Toamnei 19'
                     )

    _admin = User(first_name='Adminescu',
                  last_name='Adminovici',
                  email='admin@example.com',
                  password='admin',
                  verified=True,
                  admin=True
                  )

    # noinspection PyArgumentList
    _user = User(first_name='Utilizatorescu',
                 last_name='Userovici',
                 ngo=_ngo,
                 email='user1@example.com',
                 password='testuser',
                 verified=True,
                 admin=False)

    _donor = Donor(first_name='Donorescu',
                   last_name='Donorovici',
                   ngo=_ngo,
                   date_created=datetime.utcnow(),
                   county="IF",
                   city="Otopeni"
                   )

    db.session.add(_ngo)

    db.session.add(_admin)

    db.session.add(_user)

    db.session.add(_donor)

    db.session.commit()


@manager.command
def init_db():
    """
    Initializes all tables as per the existing models.
    """

    db.create_all()
    print('Created all tables successfully.')


@manager.command
def load_dummy():
    """
    Loads dummy data into the data model.
    """
    load_dummy_data()
    print('Successfully loaded dummy data')


@manager.command
def drop_db():
    """
    WARNING! Drops the current database.
    """

    if prompt_bool("Are you sure you want drop the entire database ?"):
        db.drop_all()

    print('Dropped the database')


if __name__ == '__main__':
    manager.run()
