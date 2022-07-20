# gr-_-krcn-game-server

# Table of contents
1. [About](#1-about)
    1. [Technologies](#11-technologies)
    2. [Screenshots](#12-screenshots)
    3. [Architecture diagram](#13-architecture-diagram)
2. [Project setup](#2-project-setup)
    1. [Docker](#21-docker)
    2. [Without Docker](#22-without-docker)
    3. [Development server](#23-development-server)
3. [Other](#3-other)
    1. [Testing](#31-testing)
    2. [Populating DB](#32-populating-db)
    3. [Creating admin (superuser)](#33-creating-admin-superuser)


# 1. About
Microservice module for handling card games and the ranking system in the web application for card games. The second one microservice is rensponsible for user accounts. Game-server storages data in PostgreSQL database which is not directly shared with other microservice. Communication between microservices uses RabbitMQ queues. Architecture is graphicly described in [Architecture diagram](README.md#12-architecture-diagram)


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

## 1.2 Screenshots
### Game interface
![obraz](https://user-images.githubusercontent.com/63737298/180075941-8ae5a86e-983b-4919-b625-d4a237b598a9.png)


### Creating lobby
![obraz](https://user-images.githubusercontent.com/63737298/180075810-06b4f8b0-66d3-40bb-a7e3-31b95de9f1a6.png)

### lobby
![obraz](https://user-images.githubusercontent.com/63737298/180075865-ef3b55df-0d38-4206-98de-024eb141b153.png)



## 1.3 Architecture diagram
TODO: translate UML diagrams to english

![obraz](https://user-images.githubusercontent.com/63737298/179372483-6ecb66ab-4849-4738-a5aa-1b15e37f5a20.png)




# 2. Project setup
## 2.1 Docker
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


## 2.2 Without Docker
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
