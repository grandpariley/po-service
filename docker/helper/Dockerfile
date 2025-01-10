FROM python:3.10
WORKDIR /code
COPY ./Pipfile* /code/
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile
COPY ./po /code/po
COPY ./poimport /code/poimport
COPY ./pomatch /code/pomatch
COPY ./*.py /code/
COPY ./helper.sh /code/
RUN chmod +x /code/helper.sh
CMD ./helper.sh