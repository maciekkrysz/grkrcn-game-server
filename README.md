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

## Development server
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
docker compose exec web python manage.py test
```

### Populating DB
```
docker compose exec web python manage.py loaddata populate.json
```

### Creating \admin\ superuser
```
docker compose exec web python manage.py createsuperuser
```