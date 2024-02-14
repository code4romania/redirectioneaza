help:                             ## Display a help message detailing commands and their purpose
	@echo "Commands:"
	@grep -E '^([a-zA-Z_-]+:.*?## .*|#+ (.*))$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""


## [Managing the project]
### Stopping the containers and dropping the databases
stop-sqlite:                      ## stops the sqlite dev project
	docker compose --profile sqlite3 down -t 60

drop-sqlite:                      ## stops the sqlite dev project
	docker compose --profile sqlite3 down -v -t 60
	rm -rf ./backend/.db_sqlite

stop-mysql:                       ## stops the mysql dev project
	docker compose --profile mysql down -t 60

drop-mysql:                       ## stops the mysql dev project
	docker compose --profile mysql down -v -t 60

stop-psql:                       ## stops the psql dev project
	docker compose --profile psql down -t 60

drop-psql:                       ## stops the psql dev project
	docker compose --profile psql down -v -t 60

stop-prod:                        ## stops the mysql dev project
	docker compose -f docker-compose.prod.yml down -t 60

drop-prod:                        ## stops the mysql dev project
	docker compose -f docker-compose.prod.yml down -v -t 60

### Building & starting the containers
up-sqlite:                        ## run the project with sqlite
	docker compose --profile sqlite3 up --build

upd-sqlite:                       ## run the project with sqlite in detached mode
	docker compose --profile sqlite3 up -d --build

up-mysql:                         ## run the project with mysql
	docker compose --profile mysql up --build

upd-mysql:                        ## run the project with mysql in detached mode
	docker compose --profile mysql up -d --build

up-psql:                         ## run the project with psql
	docker compose --profile psql up --build

upd-psql:                        ## run the project with psql in detached mode
	docker compose --profile psql up -d --build

up-prod:                         ## run the project with mysql
	docker compose -f docker-compose.prod.yml up --build

upd-prod:                        ## run the project with mysql in detached mode
	docker compose -f docker-compose.prod.yml up -d --build

### Using the SQLite database
run-sqlite: stop-psql stop-mysql up-sqlite   ## run the project with sqlite and stop the mysql project beforehand
rund-sqlite: stop-psql stop-mysql upd-sqlite ## run the project with sqlite in detached mode and stop the mysql project beforehand
redo-sqlite: drop-sqlite up-sqlite           ## delete the db and rerun the project with sqlite
redod-sqlite: drop-sqlite upd-sqlite         ## delete the db and rerun the project with sqlite in detached mode

### Using the MySQL database
run-mysql: stop-psql stop-sqlite up-mysql    ## run the project with mysql and stop the sqlite project beforehand
rund-mysql: stop-psql stop-sqlite upd-mysql  ## run the project with mysql in detached mode and stop the sqlite project beforehand
redo-mysql: drop-mysql up-mysql              ## delete the db and rerun the project with mysql
redod-mysql: drop-mysql upd-mysql            ## delete the db and rerun the project with mysql in detached mode

### Using the PostgreSQL database
run-psql: stop-mysql stop-sqlite up-psql      ## run the project with psql and stop the mysql project beforehand
rund-psql: stop-mysql stop-sqlite upd-psql    ## run the project with psql in detached mode and stop the mysql project beforehand
redo-psql: drop-psql up-psql                  ## delete the db and rerun the project with psql
redod-psql: drop-psql upd-psql                ## delete the db and rerun the project with psql in detached mode

### Other run options
run: run-sqlite                   ## set the default run command to sqlite
redo: redo-sqlite                 ## set the default redo command to sqlite
rund: rund-sqlite                 ## set the default run command to sqlite
redod: redod-sqlite               ## set the default redo command to sqlite

stop: stop-sqlite stop-mysql stop-psql stop-prod ## stop all running projects

drop: drop-sqlite drop-mysql drop-psql drop-prod ## drop all databases


## [Monitoring the containers]
logs-dev:                         ## show the logs of the containers
	docker logs -f redirect_dev

logs: logs-dev                    ## set the default logs command to dev

logs-prod:                        ## show the logs of the containers
	docker logs -f redirect_prod


## [Django operations]
makemigrations:                   ## generate migrations in a clean container
	docker exec redirect_dev sh -c "python3 -Wd ./backend/manage.py makemigrations $(apps)"

migrate:                          ## apply migrations in a clean container
	docker exec redirect_dev sh -c "python3 -Wd ./backend/manage.py migrate $(apps)"

migrations: makemigrations migrate ## generate and apply migrations

makemessages:                     ## generate the strings marked for translation
	docker exec redirect_dev sh -c "python3 -Wd ./backend/manage.py makemessages -a"

compilemessages:                  ## compile the translations
	docker exec redirect_dev sh -c "python3 -Wd ./backend/manage.py compilemessages"

messages: makemessages compilemessages ## generate and compile the translations

collectstatic:                    ## collect the static files
	docker exec redirect_dev sh -c "python3 -Wd ./backend/manage.py collectstatic --no-input"

format:                           ## format the code with black & ruff
	docker exec redirect_dev sh -c "black ./backend && ruff check --fix ./backend"

pyshell:                          ## start a django shell
	docker exec -it redirect_dev sh -c "python3 -Wd ./backend/manage.py shell"

sh:                               ## start a sh shell
	docker exec -it redirect_dev sh -c "sh"

bash:                             ## start a bash shell
	docker exec -it redirect_dev sh -c "bash"


## [Requirements management]
requirements-build:               ## run pip compile and add requirements from the *.in files
	docker exec redirect_dev sh -c " \
		cd ./backend && \
		pip-compile --strip-extras --resolver=backtracking -o requirements.txt requirements.in && \
		pip-compile --strip-extras --resolver=backtracking -o requirements-dev.txt requirements-dev.in \
	"

requirements-update:              ## run pip compile and rebuild the requirements files
	docker exec redirect_dev sh -c " \
		cd ./backend && \
		pip-compile --strip-extras --resolver=backtracking -r -U -o requirements.txt requirements.in && \
		pip-compile --strip-extras --resolver=backtracking -r -U -o requirements-dev.txt requirements-dev.in && \
		chmod a+r requirements.txt && \
		chmod a+r requirements-dev.txt \
	"


## [Clean-up]
clean-docker:                     ## stop docker containers and remove orphaned images and volumes
	docker compose --profile mysql down -t 60
	docker compose --profile psql down -t 60
	docker compose --profile sqlite3 down -t 60
	docker compose -f docker-compose.prod.yml down -t 60
	docker system prune -f

clean-extras:                        ## remove test, coverage, file artifacts, and compiled message files
	find ./backend -name '*.mo' -delete
	find ./backend -name '*.pyc' -delete
	find ./backend -name '*.pyo' -delete
	find ./backend -name '.coverage' -delete
	find ./backend -name '.pytest_cache' -delete
	find ./backend -name '.ruff_cache' -delete
	find ./backend -name '__pycache__' -delete
	find ./backend -name 'htmlcov' -delete

clean-db:                          ## remove the database files
	rm -rf ./backend/media ./backend/static ./frontend/dist

clean: clean-docker clean-extras clean-db  ## remove all build, test, coverage and Python artifacts


## [Project-specific operations]
mock-data:                        ## generate fake data
	docker exec redirect_dev python3 -Wd ./backend/manage.py generate_editions 10 --just_one_active
	docker exec redirect_dev python3 -Wd ./backend/manage.py generate_orgs 20 --active_edition
	docker exec redirect_dev python3 -Wd ./backend/manage.py generate_jury_groups 4
	docker exec redirect_dev python3 -Wd ./backend/manage.py generate_judges 16
