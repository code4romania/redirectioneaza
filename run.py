"""
Application runner on non-production environments.
"""

from redirectioneaza import app
from redirectioneaza.config import DEV_SERVER_HOST, DEV_SERVER_PORT

if __name__ == '__main__':
    app.run(host=DEV_SERVER_HOST, port=DEV_SERVER_PORT, debug=False)
