initialize_git:
	@echo "Initializing git ..."
	git init

install:
	@echo "Installing"
	pipenv install
	pipenv install pre-commit
	pipenv run pre-commit install

activate:
	@echo "activating virtual environnement"
	pipenv shell
run:
	@echo "run script"
	python app.py --config './config.yaml' >> ./log.txt

setup: initialize_git install 