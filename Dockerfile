FROM python:3.10
ENV PROJECT_DIR /usr/local/bin/src/app
RUN pip install pipenv
WORKDIR ${PROJECT_DIR}
COPY . ${PROJECT_DIR}
RUN pipenv install --system --deploy 
EXPOSE  80
CMD [ "python", "./app.py" , "--config" , "./config.yaml"]