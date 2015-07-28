


import os




# if we are currently in production
PRODUCTION = os.environ.get('SERVER_SOFTWARE', 'Development').startswith('Development')

# use this to simulate production
# PRODUCTION = True


# where all the jinja2 templates should be located
VIEWS_FOLDER = "/views"

DEV_DEPENDECIES_LOCATION = "/bower_components"
TITLE = "donez si eu"

SESSION_SECRET_KEY = ""


# ADMIN
BASE_ADMIN_LINK = "/admin"



def webapp_add_wsgi_middleware(app):
    from google.appengine.ext.appstats import recording
    app = recording.appstats_wsgi_middleware(app)
    return app

appstats_CALC_RPC_COSTS = True