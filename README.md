# Redirectioneaza 2%

[![GitHub contributors](https://img.shields.io/github/contributors/code4romania/redirectioneaza.svg?style=for-the-badge)](https://github.com/code4romania/redirectioneaza/graphs/contributors) [![GitHub last commit](https://img.shields.io/github/last-commit/code4romania/redirectioneaza.svg?style=for-the-badge)](https://github.com/code4romania/redirectioneaza/commits/master) [![License: MPL 2.0](https://img.shields.io/badge/license-MPL%202.0-brightgreen.svg?style=for-the-badge)](https://opensource.org/licenses/MPL-2.0)

* tax form #230 made easy
* digital solution for an offline process
* as simple and as efficient as possible
* helps you compare and choose who to support
* helps NGOs reach their public and keep track of their supporters

[See the project live](http://redirectioneaza.ro/)

HELPING SHOULD BE SIMPLE - Every year people can redirect 2% of their income tax to a worthy cause. However, most of them never do it, being put off by two hurdles: the bureaucratic process and the lack of information on NGOs they could help.

Moreover, NGOs themselves have a hard time getting their message across to as many people as possible.

The website will have information on a variety of NGOs that can be supported by redirecting 2% of the income tax. It will also be a means for NGOs to showcase their projects to a wider audience and convince them to re-direct the 2% to them.

Direct contact between the two will not be necessary anymore, which means saving time and resources for both and more #230 tax forms submitted.

SUPPORT A WORTHY CAUSE FOR FREE IN 5 EASY STEPS

1. browse and choose the NGO you want to redirect 2% of your income tax to
2. fill in tax form #230 online
3. print the filled in form
4. sign the form
5. mail the form to your ANAF agency

[Contributing](#contributing) | [Built with](#built-with) | [Repos and projects](#repos-and-projects) | [Deployment](#deployment) | [Feedback](#feedback) | [License](#license) | [About Code4Ro](#about-code4ro)

## Contributing

This project is built by amazing volunteers and you can be one of them! Here's a list of ways in [which you can contribute to this project](.github/CONTRIBUTING.MD).

## Built With

### Programming languages

Python27

### Platforms

Google App Engine

### Package managers

Bower

### Database technology & provider

Google Cloud Datastore

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

### Bulding new handlers

New handlers should extend `BaseHandler` from `models.handlers`. The path to the html file should be set as `template_name`. The app looks in the `views` folder for it.
To send props to the view, use the dict `self.template_values`.
On the `get` method, `self.render()` should be called at the end.

## Deployment

1. Install Google App Engine Python SDK. [Details here aici](https://cloud.google.com/appengine/docs/standard/python/download#python_linux)
2. Clone the repo: `git clone https://github.com/code4romania/redirectioneaza`
3. Install the requirements in the `lib` folder (not globally): `pip install -r requirements.txt -t ./lib`
4. `bower install`
5. Rename `app.yaml.example` to `app.yaml`
6. To run the dev server you need to know the path to the App Engine SDK and be in the app's folder:
```sh
[path_to_sdk]/dev_appserver.py ./app.yaml --datastore_path=./datastore.db --enable_console
```
Read more about the Local Development Server [here](https://cloud.google.com/appengine/docs/standard/python/tools/using-local-server).
Locally, App Engine has an interface for the DB found [here](http://localhost:8000/datastore) (the server needs to be running).

To deploy the app from the command line, run:
```sh
gcloud app deploy --no-promote ./app.yaml --version [version]
```
`version` must be the new version of the app

### Testing remotely
Google offers some generous free quota for App engine apps so you can create you own app engine app [here](http://console.cloud.google.com/appengine/) and deploy it there. You need a google account (gmail, etc.)

### Deploying indexes
When adding new `ndb` Models with indexed properties, they will be automatically added in the local file named `index.yaml`. That file needs to be deployed every time it changes. To do that, run:
```sh
gcloud app deploy ./index.yaml
```

### CSS
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

## Feedback

* Request a new feature on GitHub.
* Vote for popular feature requests.
* File a bug in GitHub Issues.
* Email us with other feedback contact@code4.ro

## License

This project is licensed under the MPL 2.0 License - see the [LICENSE](LICENSE) file for details

## About Code4Ro

Started in 2016, Code for Romania is a civic tech NGO, official member of the Code for All network. We have a community of over 500 volunteers (developers, ux/ui, communications, data scientists, graphic designers, devops, it security and more) who work pro-bono for developing digital solutions to solve social problems. #techforsocialgood. If you want to learn more details about our projects [visit our site](https://www.code4.ro/en/) or if you want to talk to one of our staff members, please e-mail us at contact@code4.ro.

Last, but not least, we rely on donations to ensure the infrastructure, logistics and management of our community that is widely spread accross 11 timezones, coding for social change to make Romania and the world a better place. If you want to support us, [you can do it here](https://code4.ro/en/donate/).
