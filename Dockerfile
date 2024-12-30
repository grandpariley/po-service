FROM python:3.10
WORKDIR /code
COPY ./Pipfile* /code/
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile
COPY ./po /code/po
COPY ./poimport /code/poimport
COPY ./pomatch /code/pomatch
COPY ./*.py /code/
CMD ["pipenv", "run", "gunicorn", "-w", "1", "-b", "0.0.0.0:2736", "--access-logfile", "-", "--error-logfile", "-", "main:app"]