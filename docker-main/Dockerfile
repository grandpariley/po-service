FROM python:3.10
WORKDIR /code
COPY ./Pipfile* /code/
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile
COPY ./po /code/po
COPY ./poimport /code/poimport
COPY ./pomatch /code/pomatch
COPY ./*.py /code/
CMD ["pipenv", "run", "python3", "main.py"]