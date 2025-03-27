docker stop jobspy-api
docker rm jobspy-api
docker build -t jobspy-api .
docker run -d --name jobspy-api -p 5000:5000 jobspy-api
