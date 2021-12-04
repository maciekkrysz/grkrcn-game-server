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


# def room(request, game_name, room_id):
#     return render(request, 'games/room.html', {
#         'room_id': room_id,
#         'game_name': game_name
#     })


def games(request):
    data = list(GameType.objects.all().values('type_name', 'description'))
    for game in data:
        game['name'] = normalize_str(game['type_name']).lower()
    request.session['cos'] = 'costam'
    request.session['cos2'] = 'costam'
    print(request.session.__dict__)
    print(request.session.get_expiry_date())
    print(datetime.now())
    if not request.session.session_key:
        request.session.save()
    return JsonResponse(data, safe=False)


def game_lobbies(request, game_name):
    print(request.session.__dict__)
    games = redis_list_from_dict('available_games', f'.{game_name}')
    games.extend(redis_list_from_dict('ongoing_games', f'.{game_name}'))
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
    print(request.session.__dict__)
    for typegame in list(GameType.objects.all().values('type_name', 'description')):
        if normalize_str(typegame['type_name']).lower() == game_name:
            typegame['name'] = game_name
            return JsonResponse(typegame, safe=False)
    return HttpResponseNotFound("Game does not exist")


@ensure_csrf_cookie
def game_create(request, game_name):
    print(request.session.__dict__)
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
    success_slo = False
    attributes = False
    paint_logout = False
    print(request.session.__dict__)


    request_id = None
    if 'AuthNRequestID' in request.session:
        request_id = request.session['AuthNRequestID']

    # auth.process_response(request_id=request_id) 
    # print(auth.get_attributes())
    if 'sso' in req['get_data']:
        return HttpResponseRedirect(auth.login())
        # If AuthNRequest ID need to be stored in order to later validate it, do instead
        # sso_built_url = auth.login()
        # request.session['AuthNRequestID'] = auth.get_last_request_id()
        # return HttpResponseRedirect(sso_built_url)
    elif 'sso2' in req['get_data']:
        print(OneLogin_Saml2_Utils.get_self_url(req))
        # return_to = OneLogin_Saml2_Utils.get_self_url(req) # api-gateway
        # return to game_id lobby
        print('------------')
        print(request.session.__dict__)
        return_to = 'localhost:8080/games/'
        print(auth.login(return_to))
        return HttpResponse(auth.login(return_to), status=401)
    elif 'acs' in req['get_data']:
        req['post_data']['SAMLResponse'] = req['get_data']['SAMLResponse']
        request_id = None
        if 'AuthNRequestID' in request.session:
            request_id = request.session['AuthNRequestID']

        auth.process_response(request_id=request_id)
        errors = auth.get_errors()
        not_auth_warn = not auth.is_authenticated()
        print(OneLogin_Saml2_Utils.TIME_FORMAT)
        print(OneLogin_Saml2_Utils.TIME_FORMAT_2)
        print(OneLogin_Saml2_Utils.TIME_FORMAT_WITH_FRAGMENT)
        # print(OneLogin_Saml2_Utils.parse_SAML_to_time('2016-06-02T13:53:14.925+01:00'))
        request.session['cos'] = 'costam'
        print(request.session)
        print(request.session.__dict__)
        print(errors)
        if not errors:
            if 'AuthNRequestID' in request.session:
                del request.session['AuthNRequestID']
            request.session.set_expiry(300)
            print(request.session.get_expiry_date())
            request.session['samlUserdata'] = auth.get_attributes()
            request.session['samlNameId'] = auth.get_nameid()
            request.session['samlNameIdFormat'] = auth.get_nameid_format()
            request.session['samlNameIdNameQualifier'] = auth.get_nameid_nq()
            request.session['samlNameIdSPNameQualifier'] = auth.get_nameid_spnq()
            request.session['samlSessionIndex'] = auth.get_session_index()
            print(req['post_data'].keys())
            print(auth.get_session_expiration())
            if not request.session.session_key:
                request.session.save()
            print(request.session.__dict__)
            return JsonResponse({'authorized': True})
            
        return JsonResponse({'authorized': False}, status=401)
            # if 'RelayState' in req['post_data'] and OneLogin_Saml2_Utils.get_self_url(req) != req['post_data']['RelayState']:
            #     # To avoid 'Open Redirect' attacks, before execute the redirection confirm
            #     # the value of the req['post_data']['RelayState'] is a trusted URL.
            #     print(req['post_data']['RelayState'])
            #     # return HttpResponseRedirect(auth.redirect_to(req['post_data']['RelayState']))
            #     return HttpResponseRedirect(auth.redirect_to('http://localhost:8000/games/attrs/'))
        # elif auth.get_settings().is_debug_active():
        #     error_reason = auth.get_last_error_reason()
    elif 'sls' in req['get_data']:
        request_id = None
        if 'LogoutRequestID' in request.session:
            request_id = request.session['LogoutRequestID']

        def dscb(): return request.session.flush()
        url = auth.process_slo(request_id=request_id, delete_session_cb=dscb)
        errors = auth.get_errors()
        if len(errors) == 0:
            if url is not None:
                # To avoid 'Open Redirect' attacks, before execute the redirection confirm
                # the value of the url is a trusted URL
                return HttpResponseRedirect(url)
            else:
                success_slo = True
        elif auth.get_settings().is_debug_active():
            error_reason = auth.get_last_error_reason()

    if 'samlUserdata' in request.session:
        paint_logout = True
        if len(request.session['samlUserdata']) > 0:
            attributes = request.session['samlUserdata'].items()
    print(req['get_data'])
    return JsonResponse({'errors': errors, 'error_reason': error_reason, 'not_auth_warn': not_auth_warn, 'success_slo': success_slo,
                                          'attributes': attributes, 'paint_logout': paint_logout})
    # return render(request, 'index.html', {'errors': errors, 'error_reason': error_reason, 'not_auth_warn': not_auth_warn, 'success_slo': success_slo,
    #                                       'attributes': attributes, 'paint_logout': paint_logout})


def attrs(request):
    print('redirected')
    print('redirected')
    print('redirected')
    print('redirected')
    print('redirected')
    print('redirected')
    print('redirected')
    print(request)
    req = prepare_django_request(request)
    auth = init_saml_auth(req)
    errors = []
    error_reason = None
    not_auth_warn = False
    success_slo = False
    attributes = False
    paint_logout = False

    # request['post_data'] = {
    #         'SAMLResponse': saml_response
    #     }
    print(req['post_data'])

    print(1)
    saml_settings = OneLogin_Saml2_Settings(
        settings=None, custom_base_path=settings.SAML_FOLDER)

    auth2 = OneLogin_Saml2_Auth(req, old_settings=saml_settings)
    # print(auth2.get_session_index())
    # print(req['post_data']['SAMLResponse'])

    request_id = None
    if 'AuthNRequestID' in request.session:
        request_id = request.session['AuthNRequestID']
    print(2)
    print(request.__dict__.keys())
    # print(request.__dict__)
    # for el in request.__dict__.items():
    #     print(el)
    #     print()
    print(request.session.__dict__.items())
    print('keys============')
    print(request.GET.keys())
    # request_id = request.GET['SAMLResponse']
    print(request.session.keys())
    print(request_id)
    print(auth.__dict__)
    # auth.process_response(request_id=request_id) 
    print('---')
    print(auth.get_session_index())
    print(auth.get_attributes())
    print('\n\n\n')
    # print(request.POST)
    paint_logout = False
    attributes = False
    paint_logout = False


    # print(request.POST)

    # saml_settings = OneLogin_Saml2_Settings(
    #     settings=None, custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    # cos = OneLogin_Saml2_Response(saml_settings,request.POST['SAMLResponse'])

    # print(cos.is_valid(request.POST))
    # print(cos.get_attributes())
    # print(cos.get_session_index())
    # print(cos.get_nameid_data())
    # print(cos.get_nameid())
    # print(cos.response)
    # time = OneLogin_Saml2_Utils.now()
    # print(OneLogin_Saml2_Utils.parse_time_to_SAML(time))
    # print(cos.validate_timestamps())

    # print(cos.get_session_not_on_or_after())
    # print()

    # print(request.session.__dict__)
    # if 'samlUserdata' in request.session:
    #     paint_logout = True
    #     if len(request.session['samlUserdata']) > 0:
    #         attributes = request.session['samlUserdata'].items()
    return JsonResponse({'attributes': ''})
    # return render(request, 'attrs.html',
    #               {'paint_logout': paint_logout,
    #                'attributes': attributes})


def metadata(request):
    # req = prepare_django_request(request)
    # auth = init_saml_auth(req)
    # saml_settings = auth.get_settings()
    # from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
    # OneLogin_Saml2_Metadata.sign_metadata()
    saml_settings = OneLogin_Saml2_Settings(
        settings=None, custom_base_path=settings.SAML_FOLDER, sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    errors = saml_settings.validate_metadata(metadata)

    if len(errors) == 0:
        resp = HttpResponse(content=metadata, content_type='text/xml')
    else:
        resp = HttpResponseServerError(content=', '.join(errors))
    return resp
