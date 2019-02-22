from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .models import Token
import json


class mymiddleware(MiddlewareMixin):
    def process_request(self, request):
        white_list = ['/', '/register', '/login', '/Config', '/Workbench', '/TaskStatus', '/TaskContent', '/SippScript', '/PythonScript']
        #white_list = []
        print(request.path)
        if request.path not in white_list and not request.path.startswith('/static/'):
            print(request.body)
            try:
                #token = request.GET.get('token', '') or request.POST.get('token', '') or json.loads(request.body).get('token', '')
                token = request.META.get("HTTP_AUTHORIZATION", '')
                print(token)
                print(7777)
                token_obj = Token.objects.filter(uuid=token).first()
                if token_obj:
                    # return JsonResponse({"code": 1000})
                    request.username = token_obj.user.username
                    #print("request.username", request.user.username)
                    pass
                else:
                    ret = {'code': 1004, 'error': "验证失败"}
                    return JsonResponse(ret)
            except Exception as e:
                ret = {'code': 1004, 'error': "请重新登陆！"}
                print(e)
                return JsonResponse(ret)

    def process_response(self, request, response):
        print(11111111)
        response['Access-Control-Allow-Origin'] = "http://localhost:8088"
        if request.method == "OPTIONS":
            response['Content-Type'] = "application/json;charset=UTF-8"
            print(response['Access-Control-Allow-Headers'])
        print(response)
        return response
