# gr-_-krcn-game-server

# 1. About
Microservice module for handling card games and the ranking system in the web application for card games. The second one microservice is rensponsible for user accounts. Game-server storages data in PostgreSQL database which is not directly shared with other microservice. Communication between microservices uses RabbitMQ queues. Architecture is graphicly describes in [Architecture diagram](README.md#12-architecture-diagram)


## 1.1 Technologies
- Python
- Django
- PostgreSQL
- Redis
- Websockets
- RabbitMQ
- Celery
- Docker/Docker compose
- PlantUML

## 1.2 Architecture diagram
TODO: translate UML diagrams to english
![obraz](https://user-images.githubusercontent.com/63737298/179371731-9fdb66fa-1385-4988-88a8-b5a03b03d7b3.png)



# 2. Project setup
## 2.1 Without docker
### Setup virtual env and pip.
```
$ virtualenv grkrcn-env
```
### Activate virtual env
Linux
```
$ source grkrcn-env/bin/activate
```
Windows
```
> grkrcn-env\bin\activate
```
### Download packages
```
$ pip install -r requirements.txt
```
### .env
Create .env file or rename .env.local to .env

## 2.2 Docker
### Build image
```
docker-compose up --build
```

### Start celery
```
docker compose exec game_server celery -A gameserver beat -l info
docker compose exec game_server celery -A gameserver worker -l info
```

### Add ranking worker
```
docker compose exec game_server python games/ranking_worker.py
```

## 2.3 Development server
### Security in production
Dont use certs (saml/certs/) from repository. To generate new certs use
```
openssl req -new -x509 -days 3652 -nodes -out sp.crt -keyout sp.key
```
In production saml/settings.json strict param MUST be set as "true"

### Do migration
```
$ python manage.py migrate
```
### Run server
```
$ python manage.py runserver
```

# 3. Other
## 3.1 Testing
```
docker compose exec game_server python manage.py test
```

## 3.2 Populating DB
```
docker compose exec game_server python manage.py loaddata populate.json
```

## 3.3 Creating \admin\ superuser
```
docker compose exec game_server python manage.py createsuperuser
```
