# Redirectioneaza

[![GitHub contributors][ico-contributors]][link-contributors]
[![GitHub last commit][ico-last-commit]][link-last-commit]
[![License: MPL 2.0][ico-license]][link-license]

- tax form #230 made easy
- digital solution for an offline process
- as simple and as efficient as possible
- helps you compare and choose who to support
- helps NGOs reach their public and keep track of their supporters

[See the project live][link-production]


[Contributing](#contributing) | [Built with](#built-with) | [Feedback](#feedback) | [License](#license) | [About Code for Romania](#about-code-for-romania)

## Contributing

This project is built by amazing volunteers, and you can be one of them. Here's a list of ways
in [which you can contribute to this project][link-contributing]. If you want to make any change to this repository,
please **make a fork first**.

Help us out by testing this project in the [staging environment][link-staging]. If you see something that doesn't quite
work the way you expect it to, open an Issue. Make sure to describe what you _expect to happen_ and _what is actually
happening_ in detail.

If you would like to suggest new functionality, open an Issue and mark it as a __[Feature request]__. Please be specific
about why you think this functionality will be of use. If you can, please include some visual description of what you
would like the UI to look like if you’re suggesting new UI elements.

## Built With

### Programming languages

- Backend: [Python3.12](https://www.python.org/)

### Platforms

- [AWS](https://aws.amazon.com/) through [Terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Frontend framework

- HTML + TailwindCSS + AlpineJS

### Package managers

- [pip-tools](https://pip-tools.rtfd.io/)
- [npm](https://www.npmjs.com/)

### Database technology & provider

- [PostgreSQL](https://www.postgresql.org/)

## Development

### Deployment without Docker

#### Prerequisites

- Python 3.12
- [NVM](https://github.com/nvm-sh/nvm?tab=readme-ov-file#installing-and-updating)
- a PostgreSQL 16.4 database (can be run with Docker)

1. Go to the root of the project
2. Run `cp .env.example .env.local` to create the environment file
3. Configure your database to run with the configuration in the `.env.local` file
    or run the database using docker with `docker compose up -d db_psql_dev` or `make rund-db`
4. Set up the Node.js environment
   1. Go to the `backend` directory
   2. Run `nvm use || nvm install` to install the Node.js version specified in the `.nvmrc` file
   3. Run `npm install` to install the Node.js dependencies
5. Set up the Python environment
   1. Create a virtual environment and activate it with `python3 -m venv venv && source venv/bin/activate`
   2. Go to the `backend` directory
   3. Run `pip install -r requirements-dev.txt` to install the Python dependencies

#### Running the project

1. Run the Django project in one terminal
   1. Go to the `backend` directory
   2. Run `source venv/bin/activate` to activate the Python virtual environment
   3. Run `django-admin runserver localhost:8000` to start the Django development server
2. Run the frontend in another terminal
   1. Go to the `backend` directory
   2. Run `nvm use` to use the Node.js version specified in the `.nvmrc` file
   3. Run `npm run dev` to start the frontend development server
3. Open http://localhost:8000 in your browser

:information_source:
**Configure whatever port works best for you.**
For Django, change the `:8000` to whatever works best for you.
For the frontend, set the `DJANGO_VITE_DEV_SERVER_PORT` variable in the `.env.local` file

:bangbang:
**In case of problems with the instructions**, please open an issue.
If you managed to find a solution, please open a PR with the changes.


### Deployment With Docker

1. Go to the root of the project
2. Run `cp .env.example .env` to create the environment file
3. Run `make run` to start the containers with an PostgreSQL database
4. Open http://localhost:8080 in your browser

## Feedback

* Request a new feature on GitHub.
* Vote for popular feature requests.
* File a bug in GitHub Issues.
* Email us with other feedback [contact@code4.ro](mailto:contact@code4.ro) or
  on [redirectioneaza@code4.ro](mailto:redirectioneaza@code4.ro).

## License

This project is licensed under the MPL 2.0 License — see the [LICENSE](LICENSE) file for details

## About Code for Romania

Started in 2016, Code for Romania is a civic tech NGO, official member of the Code for All network. We have a community
of around 2.000 volunteers (developers, ux/ui, communications, data scientists, graphic designers, devops, it security
and more) who work pro bono for developing digital solutions to solve social problems. #techforsocialgood. If you want
to learn more details about our projects [visit our site][link-code4] or if you want to talk to one of our staff
members, please e-mail us at contact@code4.ro.

Last, but not least, we rely on donations to ensure the infrastructure, logistics and management of our community that
is widely spread across 11 timezones, coding for social change to make Romania and the world a better place. If you want
to support us, [you can do it here][link-donate].


[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job.)

[ico-contributors]: https://img.shields.io/github/contributors/code4romania/redirectioneaza.svg?style=for-the-badge
[ico-last-commit]: https://img.shields.io/github/last-commit/code4romania/redirectioneaza.svg?style=for-the-badge
[ico-license]: https://img.shields.io/badge/license-MPL%202.0-brightgreen.svg?style=for-the-badge

[link-contributors]: https://github.com/code4romania/redirectioneaza/graphs/contributors
[link-last-commit]: https://github.com/code4romania/redirectioneaza/commits/main
[link-license]: https://opensource.org/licenses/MPL-2.0
[link-contributing]: https://github.com/code4romania/.github/blob/main/CONTRIBUTING.md

[link-production]: https://redirectioneaza.ro
[link-staging]: https://redirectioneaza.staging.heroesof.tech/

[link-code4]: https://www.code4.ro/en/
[link-donate]: https://code4.ro/en/donate/
