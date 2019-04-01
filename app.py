"""
Application runner on non-production environments.
"""

from redirectioneaza import app

if __name__ == '__main__':
    app.run(host=app.config['DEV_SERVER_HOST'],
            port=app.config['DEV_SERVER_PORT'],
            debug=True)
