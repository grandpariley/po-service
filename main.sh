#sudo docker build -t po-service-container .
#sudo docker run --env-file .env -p 81:80 po-service-container
pip install pipenv && pipenv install --deploy --ignore-pipfile
pipenv run fastapi run main.py --port 80
