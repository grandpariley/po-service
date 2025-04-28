FROM python:3.11
WORKDIR /code
COPY ./Pipfile* /code/
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile
COPY ./po /code/po
COPY ./poimport /code/poimport
COPY ./pomatch /code/pomatch
COPY ./image /code/image
COPY ./*.py /code/
COPY ./main.sh /code/
RUN chmod +x /code/main.sh
CMD ./main.sh