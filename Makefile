help:                                            ## Display a help message detailing commands and their purpose
	@echo "Commands:"
	@grep -E '^([a-zA-Z_-]+:.*?## .*|#+ (.*))$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""


## [Managing the project]
### Stopping the containers and dropping the databases
stop-psql:                                       ## stops the psql dev project
	docker compose -f docker-compose.yml down -t 60

drop-psql:                                       ## drops the psql dev project
	docker compose -f docker-compose.yml down -v -t 60

stop-prod:                                       ## stops the prod project
	docker compose -f docker-compose.prod.yml down -t 60

drop-prod:                                       ## drops the prod project
	docker compose -f docker-compose.prod.yml down -v -t 60

### Building & starting the containers
up-psql:                                         ## run the project with psql
	docker compose -f docker-compose.yml up --build

upd-psql:                                        ## run the project with psql in detached mode
	docker compose -f docker-compose.yml up -d --build

up-psql-db:                                      ## run only the database with psql
	docker compose -f docker-compose.yml up db_psql_dev

upd-psql-db:                                     ## run only the database with psql in detached mode
	docker compose -f docker-compose.yml up -d db_psql_dev

up-prod:                                         ## run the project with psql in production
	docker compose -f docker-compose.prod.yml up --build

upd-prod:                                        ## run the project with psql in production in detached mode
	docker compose -f docker-compose.prod.yml up -d --build

### Using the PostgreSQL database
run-psql: up-psql                                ## run the project with psql and stop the prod config beforehand
rund-psql: upd-psql                              ## run the project with psql in detached mode and stop the project project beforehand
redo-psql: drop-psql up-psql                     ## delete the db and rerun the project with psql
redod-psql: drop-psql upd-psql                   ## delete the db and rerun the project with psql in detached mode

run-psql-db: up-psql-db                          ## run the project with psql and stop the prod config beforehand
rund-psql-db: upd-psql-db                        ## run the project with psql in detached mode and stop the project project beforehand

### Using the Production configuration
run-prod: up-prod                                ## run the project with prod
rund-prod: upd-prod                              ## run the project with prod in detached mode
redo-prod: drop-prod up-prod                     ## delete the db and rerun the project with prod
redod-prod: drop-prod upd-prod                   ## delete the db and rerun the project with prod in detached mode

### Other run options
run: run-psql                                    ## set the default run command to psql
redo: redo-psql                                  ## set the default redo command to psql
rund: rund-psql                                  ## set the default run command to psql
redod: redod-psql                                ## set the default redo command to psql
run-db: run-psql-db                              ## set the default run command to psql
rund-db: rund-psql-db                            ## set the default run command to psql

stop: stop-psql stop-prod                        ## stop all running projects

drop: drop-psql drop-prod                        ## drop all databases


## [Monitoring the containers]
logs-dev:                                        ## show the logs of the containers
	docker logs -f redirect_dev

logs: logs-dev                                   ## set the default logs command to dev

logs-prod:                                       ## show the logs of the containers
	docker logs -f redirect_prod


## [Django operations]
makemigrations:                                  ## generate migrations in a clean container
	docker exec redirect_dev sh -c "cd ./backend && python3 -Wd ./manage.py makemigrations $(apps)"

migrate:                                         ## apply migrations in a clean container
	docker exec redirect_dev sh -c "cd ./backend && python3 -Wd ./manage.py migrate $(apps)"

migrations: makemigrations migrate               ## generate and apply migrations

makemessages:                                    ## generate the strings marked for translation
	docker exec redirect_dev sh -c "cd ./backend && python3 -Wd ./manage.py makemessages -a"

compilemessages:                                 ## compile the translations
	docker exec redirect_dev sh -c "cd ./backend && python3 -Wd ./manage.py compilemessages"

messages: makemessages compilemessages ## generate and compile the translations

collectstatic:                                   ## collect the static files
	docker exec redirect_dev sh -c "cd ./backend && python3 -Wd ./manage.py collectstatic --no-input"

format:                                          ## format the code with black & ruff
	docker exec redirect_dev sh -c "black ./backend && ruff check --fix ./backend"

pyshell:                                         ## start a django shell
	docker exec -it redirect_dev sh -c "cd ./backend && python3 -Wd ./manage.py shell"

sh:                                              ## start a sh shell
	docker exec -it redirect_dev sh -c "sh"

bash:                                            ## start a bash shell
	docker exec -it redirect_dev sh -c "bash"


## [Requirements management]
requirements-build:                              ## run pip compile and add requirements from the *.in files
	docker exec redirect_dev sh -c " \
		cd ./backend && \
		pip-compile --strip-extras --resolver=backtracking -o requirements.txt requirements.in && \
		pip-compile --strip-extras --resolver=backtracking -o requirements-dev.txt requirements-dev.in \
	"

requirements-update:                             ## run pip compile and rebuild the requirements files
	docker exec redirect_dev sh -c " \
		cd ./backend && \
		pip-compile --strip-extras --resolver=backtracking -r -U -o requirements.txt requirements.in && \
		pip-compile --strip-extras --resolver=backtracking -r -U -o requirements-dev.txt requirements-dev.in && \
		chmod a+r requirements.txt && \
		chmod a+r requirements-dev.txt \
	"


## [Clean-up]
clean-docker:                                    ## stop docker containers and remove orphaned images and volumes
	docker compose down -t 60
	docker compose -f docker-compose.yml down -t 60
	docker compose -f docker-compose.prod.yml down -t 60
	docker system prune -f

clean-extras:                                    ## remove test, coverage, file artifacts, and compiled message files
	find ./backend -name '*.mo' -delete
	find ./backend -name '*.pyc' -delete
	find ./backend -name '*.pyo' -delete
	find ./backend -name '.coverage' -delete
	find ./backend -name '.pytest_cache' -delete
	find ./backend -name '.ruff_cache' -delete
	find ./backend -name '__pycache__' -delete
	find ./backend -name 'htmlcov' -delete
	find ./backend -name '.bower_components' -delete

clean-db:                                        ## remove the database files
	rm -rf ./backend/media ./backend/static ./frontend/dist

clean: clean-docker clean-extras clean-db        ## remove all build, test, coverage and Python artifacts


## [Project-specific operations]
mock-data:                                       ## generate fake data
	docker exec redirect_dev cd ./backend && python3 -Wd ./manage.py generate_orgs 20
	docker exec redirect_dev cd ./backend && python3 -Wd ./manage.py generate_orgs 50 --valid
	docker exec redirect_dev cd ./backend && python3 -Wd ./manage.py generate_partners 5
	docker exec redirect_dev cd ./backend && python3 -Wd ./manage.py generate_donations 100


## [Tests]
tests:                            ## run the tests
	docker exec redirect_dev sh -c " \
		cd ./backend && python3 -Wd manage.py test \
	"
