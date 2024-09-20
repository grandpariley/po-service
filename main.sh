sudo docker build -t po-service-container .
sudo docker run --env-file .env -p 81:80 po-service-container
