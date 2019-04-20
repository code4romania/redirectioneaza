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

Flask 1.0.2 / Python 3.7

### Package managers

Bower

### Database technology & provider

PostgreSQL / SQLAlchemy

## App structure

The entry point of the app is `app.py`. 
All the routes are defined in `redirectioneaza\routes.py`.

The application itself is located in the folder `redirectioneaza`.


Its main components are
* `controllers`  this module contains the views for each route
* `handlers` this module contains the following helpers:
    * `pdf` the logic for creating the pdf
    * `email` a small wrapper over SendGrid
    * `base` contains the base view handler from which all views should inherit
    * `captcha` the logic behind captcha validation on pages with forms
    * `utils` utilities  
* `static` all the static files: css, js, images
* `templates` all the html files + email templates. New html pages should extend `base.html`
* `config.py` configuration data
* `core.py` defines the core objects such as app, db and login_manager
* `routes.py` defines all the routes used by the app

### Bulding new handlers

New handlers should extend `BaseHandler` from `handlers.base`. 

The path to the html file should be set as `template_name`. The app looks in the `views` folder for it.
To send props to the view, use the dict `self.template_values`.

## Deployment

1. Clone the repo into a folder: `git clone https://github.com/code4romania/redirectioneaza`
2. Set up a virtual env `virtualenv venv` and activate it `source venv/bin/activate`
3. Install the requirements : `pip install -r requirements.txt`
4. Install front-end development assets `bower install`
5. Initialize the database and populate with dummy data:

`python3 manage.py init_db` then
`python3 manage.py load_dummy`

6.  To run the application, run:
`python3 app.py`

The app will be ran by default on `localhost:5000`.

### CSS
The app uses `LESS`. To compile the CSS, run:
```sh
cd ./static/
lessc css/main.less > css/main.css --clean-css="--s1 --advanced --compatibility=ie8"
```

### Migrations

For database migrations, use the commands for [Flask-Migrate](https://flask-migrate.readthedocs.io/en/latest/).
`python3 manage.py migrations` - will display a list of available commands, whereas for example `python3 manage.py migrations init` would set up the initial migration.

### Tests

To run tests:
1. `cd tests`
2. `pytest`

This will run both unit and selenium/integration testing. To run a particular set of tests or a particular tests run `pytest test_app` and e.g. `pytest test_app.py::test_name` respectively.

### Read more
You can read more about the frameworks used by the app:
* [flask](http://flask.pocoo.org/)
* [jinja2](http://jinja.pocoo.org/docs/dev/templates/)

## Feedback

* Request a new feature on GitHub.
* Vote for popular feature requests.
* File a bug in GitHub Issues.
* Email us with other feedback [contact@code4.ro](mailto:contact@code.ro)

## License

This project is licensed under the MPL 2.0 License - see the [LICENSE](LICENSE) file for details

## About Code4Ro

Started in 2016, Code for Romania is a civic tech NGO, official member of the Code for All network. We have a community of over 500 volunteers (developers, ux/ui, communications, data scientists, graphic designers, devops, it security and more) who work pro-bono for developing digital solutions to solve social problems. #techforsocialgood. If you want to learn more details about our projects [visit our site](https://www.code4.ro/en/) or if you want to talk to one of our staff members, please e-mail us at contact@code4.ro.

Last, but not least, we rely on donations to ensure the infrastructure, logistics and management of our community that is widely spread accross 11 timezones, coding for social change to make Romania and the world a better place. If you want to support us, [you can do it here](https://code4.ro/en/donate/).
