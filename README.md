# 2%

## Setup
1. Install Google App Engine Python SDK. [Details here aici](https://cloud.google.com/appengine/docs/standard/python/download#python_linux)
2. Clone the repo: `git clone https://github.com/code4romania/redirectioneaza`
3. Install the requirements in the `lib` folder (not globally): `pip install -r requirements.txt -t ./lib`
4. `bower install`
5. To run the dev server you need to know the path to the App Engine SDK and be in the app's folder:
```sh
[path_to_sdk]/dev_appserver.py ./app.yaml --datastore_path=./datastore.db --enable_console
```
Read more about the Local Development Server [here](https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server).
Locally, App Engine has an interface for the DB found [here](http://localhost:8000/datastore) (the server needs to be running).

## App structure
The entry point of the app is `main.py`. Here is where all the routes are defined.
The main folders are:
* `controllers` contains the handlers for each route
* `models` has the `ndb` Models and some helpers:
    * `create_pdf` the logic for creating the pdf
    * `email` a small wrapper over SendGrid
    * `handlers` wrappers over `webapp2.RequestHandler`, they add some functionality. New handlers should inherit from `BaseHandler` or `AccountHandler`.
    * `storage` contains `CloudStorage` which helps with uploading the PDFs to google cloud
* `static` all the static files: css, js, images
* `views` all the html file + email templates. New html pages should extend `base.html`

## Bulding new handlers
New handlers should extend `BaseHandler` from `models.handlers`. The path to the html file should be set as `template_name`. The app looks in the `views` folder for it. 
To send props to the view, use the dict `self.template_values`. 
On the `get` method, `self.render()` should be called at the end.

## Notes

### Deploying
To deploy the app from the command line, run:
```sh
gcloud app deploy --no-promote ./app.yaml --version [version]
```
`version` must be the new version of the app

#### Testing remotely
Google offers some generous free quota for App engine apps so you can create you own app engine app [here](http://console.cloud.google.com/appengine/) and deploy it there. You need a google account (gmail, etc.)

#### Deploying indexes
When adding new `ndb` Models with indexed properties, they will be automatically added in the local file named `index.yaml`. That file needs to be deployed every time it changes. To do that, run:
```sh
gcloud app deploy ./index.yaml
```

#### CSS
The app uses `LESS`. To compile the CSS, run:
```sh
cd ./static/
lessc css/main.less > css/main.css --clean-css="--s1 --advanced --compatibility=ie8"
```

### Deploying CRON jobs
To deploy the new cron jobs you need to uncomment the `application` in app.yaml and change it to your app's name (this is used only in this case)
```sh
[path_to_sdk]/appcfg.py update_cron ./
```
### Adding dummy NGOs
When you start if you might want to add some ngos. Go to the sdk's [Console](http://localhost:8000/console) and run:
```python
from models.models import NgoEntity

ngo = NgoEntity(
    logo= "https://code4.ro/wp-content/uploads/2016/06/fb.png",
    name= "Nume asociatie",
    description= "O descriere",
    id= "nume-asociatie", # this needs to be unique. Also used as the ngo's URL
    account = "RO33BTRL3342234vvf2234234234XX",
    cif = "3333223",
    address = "Str. Ion Ionescu, nr 33"
)
ngo.put()
```
You can also add ngos from the admin.

### Read more
You can read more about the frameworks used by the app:
[webapp2](https://webapp2.readthedocs.io/en/latest/)
[jinja2](http://jinja.pocoo.org/docs/dev/templates/)
