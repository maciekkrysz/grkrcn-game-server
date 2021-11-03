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
