# gr-_-krcn-game-server


## Project setup
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

## Development server
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


## Docker launch
### Build image
```
docker-compose up --build
```

### Testing
```
docker compose exec game_server python manage.py test
```

### Populating DB
```
docker compose exec game_server python manage.py loaddata populate.json
```

### Creating \admin\ superuser
```
docker compose exec game_server python manage.py createsuperuser
```