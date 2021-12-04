from datetime import datetime
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from django.http import JsonResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseServerError
from .classes.games_handler import create_game
from .models import GameType
from .resources import normalize_str
from .redis_utils import redis, redis_list_from_dict, redis_game_info
import json
from django.views.decorators.csrf import ensure_csrf_cookie

from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.settings import OneLogin_Saml2_Settings
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from onelogin.saml2.response import OneLogin_Saml2_Response


def init_saml_auth(req):
    auth = OneLogin_Saml2_Auth(req, custom_base_path=settings.SAML_FOLDER)
    return auth


def prepare_django_request(request):
    # If server is behind proxys or balancers use the HTTP_X_FORWARDED fields
    result = {
        'https': 'on' if request.is_secure() else 'off',
        'http_host': request.META['HTTP_HOST'],
        'script_name': request.META['PATH_INFO'],
        'get_data': request.GET.copy(),
        'post_data': request.POST.copy()
    }
    return result


def games(request):
    data = list(GameType.objects.all().values('type_name', 'description'))
    for game in data:
        game['name'] = normalize_str(game['type_name']).lower()
    request.session['cos'] = 'costam'
    request.session['cos2'] = 'costam'
    if not request.session.session_key:
        request.session.save()
    return JsonResponse(data, safe=False)


def game_lobbies(request, game_name):
    games = redis_list_from_dict('games', f'.{game_name}')
    games_to_send = []
    for game in games:
        id, _ = game.popitem()
        game_info = redis_game_info('games', game_name, id)
        games_to_send.append(game_info)
    return JsonResponse({'lobbies': games_to_send})


def lobby_info(request, game_name, game_id):
    info = redis_game_info('games', game_name, game_id)
    return JsonResponse({'data': info})


def game_info(request, game_name):
    for typegame in list(GameType.objects.all().values('type_name', 'description')):
        if normalize_str(typegame['type_name']).lower() == game_name:
            typegame['name'] = game_name
            return JsonResponse(typegame, safe=False)
    return HttpResponseNotFound("Game does not exist")


@ensure_csrf_cookie
def game_create(request, game_name):
    if request.method == 'GET':
        try:
            with open(f'games/games_configs/{game_name}.json') as json_file:
                data = json.load(json_file)
            return JsonResponse(data)
        except:
            return HttpResponseNotFound("Game does not exist")
    elif request.method == 'POST':
        # CREATE GAME
        try:
            game_id = create_game(game_name, json.loads(request.body))
            return JsonResponse({'game_id': game_id})
        except:
            return HttpResponseBadRequest("Cannot create game")
    return JsonResponse({})


def saml_view(request):

    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False

    request_id = None
    if 'AuthNRequestID' in request.session:
        request_id = request.session['AuthNRequestID']

    if 'sso2' in req['get_data']:
        print(OneLogin_Saml2_Utils.get_self_url(req))
        # return_to = OneLogin_Saml2_Utils.get_self_url(req) # api-gateway
        # return to game_id lobby
        return_to = 'localhost:8080/games/'
        return HttpResponse(auth.login(return_to), status=401)
    elif 'acs' in req['get_data']:
        req['post_data']['SAMLResponse'] = req['get_data']['SAMLResponse']
        request_id = None
        if 'AuthNRequestID' in request.session:
            request_id = request.session['AuthNRequestID']

        auth.process_response(request_id=request_id)
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()
        request.session['cos'] = 'costam'
        if not errors:
            if 'AuthNRequestID' in request.session:
                del request.session['AuthNRequestID']
            request.session.set_expiry(300)
            request.session['samlUserdata'] = auth.get_attributes()
            request.session['samlNameId'] = auth.get_nameid()
            request.session['samlNameIdFormat'] = auth.get_nameid_format()
            request.session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
            request.session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
            request.session['samlSessionIndex'] = auth.get_session_index()
            if not request.session.session_key:
                request.session.save()
            return JsonResponse({'authorized': True})

        return JsonResponse({'authorized': False}, status=401)

    return JsonResponse({'errors': errors, 'error_reason': error_reason, 'not_auth_warn': not_auth_warn})


def metadata(request):
    saml_settings = OneLogin_Saml2_Settings(
        settings=None, custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type='text/xml')
    else:
        resp = HttpResponseServerError(content=', '.join(errors))
    return resp
