from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, prompt_bool

from core import app, db
from utils import load_dummy_data

manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command('migrations', MigrateCommand)


@manager.command
def initdb():
    """
    Initializes all tables as per existing models.
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
def dropdb():
    """
    Drops the current database.
    """

    if prompt_bool("Are you sure you want drop the entire database ?"):
        db.drop_all()


print('Dropped the database')

if __name__ == '__main__':
    manager.run()
