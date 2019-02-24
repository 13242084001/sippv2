from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, StreamingHttpResponse
from django.views import View
from .models import User, Token, tbl_sys, tbl_sipcfg, tbl_task, tbl_stat
import uuid
import json
import os, subprocess, shutil, time, datetime
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from .tasks import getSystemVersion
from app01 import serialize
from django.db.models import F

# Create your views here.

class RegisterSerialize(serializers.Serializer):
    username = serializers.CharField(max_length=16, required=True, allow_blank=False, error_messages={
        "blank": "用户名不能为",
        "max_length": "最大长度为16位",
        "required": "用户名不能为空",
    })
    password = serializers.CharField(max_length=16, required=True, allow_blank=False, error_messages={
        "max_length": "最大长度为16位",
        "blank": "密码不能为空",
    })

    #   aa = serializers.SerializerMethodField() 多对多
    #   如果有一对多字段，需要加上source="关联表.字段";如果有多对多字段，要定义一个函数，get_aa(self, obj), 把obj传进去，返回一个
    #   需要的列表或者字符串，都行, obj就是quryset, 或者模型对象

    def validate_username(self, username):
        self.user_exsit = False
        if User.objects.filter(username=username).first():
            self.user_exsit = True
            raise serializers.ValidationError("用户名已存在")
        return username

    """def validate(self, errors):
        if True:
            del errors['password']
            #raise serializers.ValidationError("1111")
        return errors
    """


class LoginSerialize(serializers.Serializer):
    username = serializers.CharField(max_length=16, required=True, allow_blank=False, error_messages={
        "blank": "用户名不能为空",
        "max_length": "最大长度为16位",
    })
    password = serializers.CharField(max_length=32, required=True, allow_blank=False, error_messages={
        "max_length": "最大长度为16位",
        "blank": "密码不能为空",
    })



class Login(APIView):
    def get(self, request, *args, **kwargs):
        return Response(None)

    def post(self, request, *args, **kwargs):
        print(22222)
        print(request.body, request.data)

        username = request.data.get('username')
        password = request.data.get('password')
        print(username, password)
        loginSerialize = LoginSerialize(data=request.data)
        ret = {"code": 10000, "token": None, "error": None}
        if loginSerialize.is_valid():
            obj = User.objects.filter(username=username).filter(password=password).first()
            if obj:
                uid = uuid.uuid3(uuid.NAMESPACE_DNS, username)
                Token.objects.update_or_create(user=obj, defaults={'uuid': uid})
                ret['token'] = uid
                response = Response(ret)
                response['Token'] = uid
                return response
            else:
                ret["code"] = 10001
                ret["error"] = "用户名或密码错误"
                return Response(ret)
        ret['code'] = 10002
        ret['error'] = loginSerialize.errors
        return Response(ret)


class user(APIView):  # 其实对于简单需求， 用django的view 或者restframework的apiview都行
    def get(self, request):
        userObj = User.objects.all()
        loginSerialize = LoginSerialize(userObj, many=True)
        print(loginSerialize.data)
        # return JsonResponse(loginSerialize.data, safe=False)
        return Response(loginSerialize.data)  # view-->JsonResponse;safe=False

    def post(self, request):
        print(request.body)
        # json.loads(request.body)
        registerSeializeObj = RegisterSerialize(data=json.loads(request.body))
        # print(loginSeializeObj.data, type(loginSeializeObj.data))

        print(registerSeializeObj.is_valid())
        print(registerSeializeObj.data, type(registerSeializeObj.data))
        ret = {'code': 10000, 'data': None, 'error': None}
        if registerSeializeObj.is_valid():
            print(registerSeializeObj.data)
            ret['data'] = registerSeializeObj.data
            # return JsonResponse(ret)
            return Response(ret)  # apiview --> Response,JsonResponse
        print(registerSeializeObj.errors, 77777)
        ret['error'] = registerSeializeObj.errors
        ret['code'] = 10001
        return Response(ret)


class Register(APIView):
    """def get(self, request):
        loginSerialize = LoginSerialize()
        print("这里是注册是get方法")
        return Response(loginSerialize.data)
    """

    def post(self, request):
        ret = {'code': 10000, 'data': None, 'error': None}
        RegisterSeializeObj = RegisterSerialize(data=json.loads(request.body))
        if RegisterSeializeObj.is_valid():
            #   data = loginSeializeObj.save()
            username = json.loads(request.body).get("username")
            data = RegisterSeializeObj.validated_data
            obj = User.objects.create(**data)
            uid = uuid.uuid3(uuid.NAMESPACE_DNS, username)
            Token.objects.update_or_create(user=obj, uuid=uid, defaults=None)

            if not os.path.exists("./Script/%s" % username):
                os.makedirs("./Script/%s" % username)
            ret['data'] = RegisterSeializeObj.validated_data
            response = Response(ret)
            response['Token'] = uid
            return response
        ret['code'] = 10004
        ret['error'] = RegisterSeializeObj.errors
        return Response(ret)


class changePasswd(APIView):
    def post(self, request):
        print(request.data)
        try:
            User.objects.filter(username=request.username, password=request.data.get('oldPasswd')).update(password=request.data.get('newPasswd'))
            return Response({'code': 10000, 'error': None})
        except Exception as e:
            return Response({'code': 10001, 'error': str(e)})



"""目录处理类"""
"""
本来想存数据库，但是查询涉及打递归查询，处理太复杂，放弃
class SippScriptPathTree(APIView):
    def get(self, request):
        user_obj = User.objects.filter(username=request.username).first()
        print(user_obj.username)
        obj = resource.objects.filter(user=user_obj).all()

        from .serialize import SippScriptSerialize
        bs = SippScriptSerialize(obj, many=True)
        print(obj.values())
        return Response(bs.data)

    def post(self, request):
        pass
"""


class SippScript(APIView):
    def post(self, request, *args, **kwargs):
        print("sssssssss")
        if kwargs.get('slug', '') == "newDir":
            return self.newDir(request)
        if kwargs.get('slug', '') == "upload":
            return self.upload(request)
        if kwargs.get('slug', '') == "download":
            return self.download(request)
        if kwargs.get('slug', '') == "getPathTree":
            return self.getPathTree(request)
        if kwargs.get("slug", '') == "ScriptInfo":
            return self.ScriptInfo(request)
        if kwargs.get('slug', '') == "DeleteScript":
            return self.DeleteScript(request)
        if kwargs.get('slug', '') == "DeleteDir":
            return self.DeleteDir(request)
        if kwargs.get('slug', '') == 'viewScript':
            return self.viewScript(request)

    # 新建文件夹
    def newDir(self, request):
        """需要两个键值对，dirname：[]， dirpath: str"""
        ret = {}
        print("sssss")
        # print(request.username)
        print(request.data)
        try:
            dirName = request.data.get('dirName')
            dirPath = request.data.get('dirPath')
            print(dirPath, dirName)
            #   Path = lambda x: "/".join(x) if len(x) > 1 else str(x)

            # if not os.path.exists('./Script/%s' % ("/".join(dirPath) + "/" + dirName)):
            #   os.makedirs('./Script/%s' % ("/".join(dirPath) + "/" + dirName))
            if not os.path.exists(dirPath + '/' + dirName):
                os.makedirs(dirPath + '/' + dirName)
                ret = {"code": 10000, "date": request.data, "error": None}
        except Exception as e:
            ret = {"code": 10001, "date": None, "error": str(e)}
        return Response(ret)

    """每个用户都要有自己的目录， 可以上传自己脚本，xml/csv/pcap"""

    # 前端通过ajax提交文件
    def upload(self, request):
        """请求体需要文件以及 目标文件目录"""
        print("dddd")
        # 测试，curl localhost:8088/upload/ -F "file=@/Users/a/PycharmProjects/sippv2/aaa.py" -F 'data={"dstpath": "/Users/a/PycharmProjects/sippv2/Script/doris"}'
        #dstpath = json.loads(request.POST.get('data'))['dstpath']
        dstpath = request.POST.get('dstpath')
        print(dstpath)
        file_obj = request.FILES.get("file")
        try:
            with open(dstpath + "/" + file_obj.name, 'wb') as f:
                for chunk in file_obj.chunks():
                    f.write(chunk)
                ret = {"code": 10000, "error": None}
        except Exception as e:
            ret = {"code": 10000, "error": str(e)}
        return Response(ret)

    # 缓冲形式下载文件
    def read_file(self, fileName):
        chunk_size = 512
        with open(fileName, 'rb') as f:
            while True:
                stream = f.read(chunk_size)
                if stream:
                    yield stream
                else:
                    break

    # 下载文件接口
    def download(self, request):
        dirPath = request.data.get('dirPath')
        print(8888)
        fileName = request.data.get('fileName')
        print(999)
        filePath = dirPath + "/" + fileName
        print(000)
        response = StreamingHttpResponse(self.read_file(filePath))
        print(response)
        response['Content-Type'] = 'application/octet-stream'
        print(111)
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(fileName)
        response['Access-Control-Expose-Headers'] = "Content-Disposition"
        print(222)
        print(response)
        return response

    def viewScript(self, request):
        dirPath = request.data.get('dirPath')
        print(8888)
        fileName = request.data.get('fileName')
        print(999)
        filePath = dirPath + "/" + fileName
        print(000)
        with open(filePath, 'rb') as f:
            str = f.read()
            print(str)
        return Response({"code": 10000, "data": str, 'error': None})

    # 获取目录树，返回json格式，前后端都用递归处理；这里资源写数据库很难处理，所以不存库
    def getPathTree(self, request):
        """以当前用户注册时生成的同名目录作为查询路劲"""
        """"""
        # curl -H "contenttype: application/json" localhost:8088/SippScript\!getPathTree -XPOST -d '{"dirpath": ""}'
        # {"code":10000,"data":[{"pathName":"doris","nodes":[],"tags":1},{"pathName":"admin","nodes":[{"pathName":"bbb","nodes":[],"tags":0},{"pathName":"aaa","nodes":[],"tags":1}],"tags":1},{"pathName":"andy","nodes":[],"tags":0}],"error":null}
        # username = request.username
        username = "admin"
        # dirPath = request.data.get("dirPath", '')
        dirPath = "admin"
        print(request.data)
        rootPath = "./Script/" + dirPath
        from .serialize import list_dir
        # 递归查询函数，返回一个字典类型数据
        pathTree = list_dir(rootPath)
        print(pathTree)
        ret = {"code": 10000, "data": pathTree, "error": None}
        return Response(ret)

    # 获取脚本列表
    def ScriptInfo(self, request):
        """{"order":"asc","limit":10,"offset":0,"dirPath":["admin"],"type":".xml"}"""
        from .serialize import getFilesInfo
        print(request.data)
        try:
            result = getFilesInfo(request)
            ret = {"code": 10000, "result": result, "error": None}
        except Exception as e:
            ret = {"code": 10002, "result": {}, "error": str(e)}
        return Response(ret)

    # 删除脚本或者目录
    def DeleteScript(self, request):
        """{"dirPath":["admin"],"script_list":["uac1.xml"]}；删除脚本根删除目录同一个接口"""
        dirPath = request.data.get('dirPath', '')
        print(request.data)
        try:

            scriptList = request.data.get('script_list')
            if scriptList:
                for i in scriptList:
                    os.remove(dirPath + '/' + i)

            return Response({'code': 10000, 'error': None})
        except Exception as e:
            return Response({'code': 10004, 'error': str(e)})

    def DeleteDir(self, request):
        """{"dirPath":["admin"],"script_list":["uac1.xml"]}；删除脚本根删除目录同一个接口"""
        dirPath = request.data.get('dirPath', '')
        print(request.data)
        try:

            shutil.rmtree(dirPath)
            return Response({'code': 10000, 'error': None})
        except Exception as e:
            return Response({'code': 10004, 'error': str(e)})


class WorkBench(APIView):
    """
    工作台界面处理类，提供两个接口
    一个是获取cpu/内存/磁盘等的使用量以及系统等
    另一个是刷新操作，刷新除了获取基本信息之外，还需要调系统接口，实时刷新系统信息
    """

    def get(self, request, *args, **kwargs):
        print(request.path)
        print("slug", kwargs)
        slug = kwargs.get('slug')
        if slug == "getDate":
            return self.getDate()
        elif slug == "refresh":
            return self.refresh()
        return Response(None)

    def test(self, res_data):
        tmp = ["cpu_rate", "mem_rate", "disk_rate", "rx_rate", "tx_rate"]
        for i in tmp:
            if res_data[i] > 0:
                res_data[i.split("_")[0] + "_status"] = "up"
            elif res_data[i] < 0:
                res_data[i.split("_")[0] + "_status"] = "down"
            else:
                res_data[i.split("_")[0] + "_status"] = "-"
            res_data[i] = abs(res_data[i])
        return res_data

    def getDate(self):
        """
        获取工作台信息，普通get请求
        :return: Json
        """
        print("**********")
        ret = {"code": 10000}
        data = {"callRate": [], 'countTime': [], 'currentCallNum': []}
        sys_data = list(tbl_sys.objects.order_by('-id')[:300].values("currCpu", "currMem", "currDisk", "curr_rx", "curr_tx", "currentConNum", "currentCps", "sysTime"))
        print(sys_data)
        sys_data.reverse()
        for item in sys_data:
            for k, v in item.items():
                if data.get(k):
                    data[k].append(v)
                else:
                    data[k] = []
                    data[k].append(v)

        try:
            taskObj = tbl_task.objects.all().last()
            chartObj = list(tbl_stat.objects.filter(taskPk_id=taskObj.id).all().values_list('callRate', 'countTime', 'currentCallNum'))
            for item in chartObj:
                data["callRate"].append(item[0])
                data["countTime"].append(item[1])
                data['currentCallNum'].append(item[2])
            data['taskName'] = taskObj.taskName
        except Exception:
            pass

        ret["error"] = None
        ret['data'] = data
        print(ret)
        return Response(ret)

    def refresh(self):
        """
        刷新操作
        :return: Json
        """
        return self.getDate()


class Config(APIView):
    """配置相关接口"""

    def get(self, request, *args, **kwargs):
        if kwargs.get('slug') == 'getUsablePortList':
            return self.getUsablePortList()
        if kwargs.get('slug') == 'getSysConfig':
            return self.getSysConfig()
        if kwargs.get('slug') == 'reset':
            return self.reset()

    def post(self, request, *args, **kwargs):
        if kwargs.get('slug') == 'getSippConfig':
            return self.getSippConfig(request)
        if kwargs.get('slug') == 'createSipCfg':
            return self.createSipCfg(request)
        if kwargs.get('slug') == 'deleteSipCfg':
            return self.deleteSipCfg(request)
        if kwargs.get('slug') == 'UpdateSipCfg':
            return self.UpdateSipCfg(request)
        if kwargs.get('slug') == 'saveSysConfig':
            return self.saveSysConfig(request)

    def createSipCfg(self, request):
        data = request.data
        print(data)
        ret = {"code": 10000, "data": request.data, "error": None}
        try:
            user = User.objects.filter(username="admin").first()  # request.username
            tbl_sipcfg.objects.create(**data, user=user)
            sys_obj = tbl_sys.objects.last().port_list
            #   sys_obj = sys_obj.split(',')
            #   sys_obj.remove(request.data.get('localPort'))
            #   sys_obj = ",".join(sys_obj)
            #   tbl_sys.objects.filter(pk=1).update(port_list=sys_obj)
        except Exception as e:
            ret['code'] = 10001
            ret['error'] = str(e)
        return Response(ret)

    def getSippConfig(self, request):
        # user = User.objects.filter(username=request.username)
        print(request.data)
        try:
            limit = request.data.get('limit')
            offset = request.data.get('offset')
            user = User.objects.filter(username="admin").first()
            sip_obj = tbl_sipcfg.objects.filter(user=user).values()
            ret = {'code': 10000, 'total': sip_obj.count(), 'data': sip_obj[int(offset):int(offset) + int(limit)],
                   'error': None}

        except Exception as e:
            ret = {'code': 10004, 'error': str(e)}
        return Response(ret)

    def getUsablePortList(self):
        portListObj = tbl_sys.objects.first().port_list
        portList = portListObj.split(',')[:-1]
        portList = map(lambda x: {'value': x}, portList)  # 把map转换成list后
        return Response({'code': 10000, 'data': portList, 'error': None})

    def deleteSipCfg(self, request):
        print(request.data)
        # 这里用拿到数据id值的列表，使用orm in查询删除
        tbl_sipcfg.objects.filter(id__in=request.data.get('deletePortList')).delete()
        # 将数据删除后，要将可用端口列表更新
        # init()  # 调用初始化可用端口列表函数
        return Response({'code': 10000, 'data': None, 'error': None})

    #   更新sip配置，{'id': 18, 'localPort': '5060', 'remoteAddr': '192.168.1.123', 'remotePort': '4556'}
    def UpdateSipCfg(self, request):
        print(request.data)
        ret = {}
        try:
            tbl_sipcfg.objects.filter(id=request.data.get('id')).update(**request.data)  #
            ret['code'] = 10000
            ret['data'] = request.data
            ret['error'] = None
        except Exception as e:
            ret['code'] = 10001
            ret['error'] = str(e)
        print(ret)
        return Response(ret)

    def getSysConfig(self):
        serverIp, localStartSipPort, usablePortCount, concurrencyNum = serialize.readingConfig("config.ini")
        return Response({'code': 10000,
                         'data':
                             {'serverIp': serverIp,
                              'localStartSipPort': localStartSipPort,
                              'usablePortCount': usablePortCount,
                              'concurrencyNum': concurrencyNum
                              },
                         'error': None
                         })

    def saveSysConfig(self, request):
        print(request.data)
        try:
            if serialize.writingConfig('config.ini', **request.data):
                return Response({'code': 10000, 'data': request.data, 'error': None})
        except Exception as e:
            return Response({'code': 10001, 'data': request.data, 'error': str(e)})

    def reset(self):
        pass


class TaskStatus(APIView):
    """任务状态"""
    def get(self, request, *args, **kwargs):
        if kwargs.get('slug') == 'getRouteOptions':
            return self.getRouteOptions()
        if kwargs.get('slug') == 'getTaskList':
            return self.getTaskList(request)

    def post(self, request, *args, **kwargs):
        """创建任务"""
        if kwargs.get('slug') == 'newTask':
            return self.newTask(request)
        if kwargs.get('slug') == 'stopTask':
            return self.stopTask(request)
        if kwargs.get('slug') == 'getTaskInfo':
            return self.getTaskInfo(request)
        if kwargs.get('slug') == 'delTask':
            return self.delTask(request)
        if kwargs.get('slug') == 'handleTask':
            return self.handleTask(request)

    # 获取sip路由配置
    def getRouteOptions(self):
        try:
            user = User.objects.filter(username='admin').first()
            obj = tbl_sipcfg.objects.filter(user=user, isRunning=False).values()
            options = []
            for item in obj:
                options.append({"id": item['id'], "value": item['localPort'] + "<==>" + item['remoteAddr'] + ":" + item['remotePort']})
            return Response({'code': 10000, 'data': options, 'error': None})
        except Exception as e:
            return Response({'code': 10001, 'error': str(e)})

    def newTask(self, request):
        print(request.data)
        print(request.data.get('increaseTime'))
        taskName = request.data.get('taskName')
        user = User.objects.filter(username=request.username).first()
        if tbl_task.objects.filter(user=user).filter(taskName=taskName).first():
            return Response({'code': 10001, 'error': '任务已存在'})
        localPort, remoteSock = request.data.get('callRoute').split('<==>')
        #   stdOut = subprocess.getstatusoutput("lsof -i -P|awk '{print $9}'|cut -d':' -f2|grep -w %s" % localPort)
        #   用shell太慢，打算换scapy，但是scapy探测本机端口抓不到包，并且无法应答，于是用nmap专业的linux端口探测工具
        stdOut = subprocess.getstatusoutput("sudo nmap 127.1 -sU -pU:%s|grep %s|awk -F' ' '{print $2}'" % (localPort, localPort))
        print(stdOut)
        if stdOut[1] != 'closed':
            return Response({'code': 10002, 'error': "端口%s被占用!" % localPort})
        # 查看当前系统总的呼叫并发数
        currentConNum  = tbl_sys.objects.filter().first().currentConNum
        # 查看当前系统配置最大并发数
        serverIp, localStartSipPort, usablePortCount, concurrencyNum = serialize.readingConfig("config.ini")
        if request.data.get('beginConcurrentNum') + currentConNum > int(concurrencyNum):
            return Response({'code': 10003, 'error': "当前系统呼叫并发数为%s, 新增呼叫后大于系统最大呼叫上限%s"% (currentConNum, concurrencyNum)})
        try:
            taskId = tbl_task.objects.all().last().taskId + 1
        except Exception:
            taskId = 1
        print(taskId, "#######")
        # 创建任务目录， 拷贝xml文件
        if not os.path.exists('./Task/%s' % taskId):
            os.makedirs('./Task/%s' % taskId)
        xmlScript = request.data.get('xmlScript')
        shutil.copy(os.path.join(request.data.get('dirPath'), xmlScript),
                    './Task/%s' % taskId)
        # 拼接sipp命令
        sippCmd = "sudo sipp -sf %s -i %s -p %s %s -r %s" % \
                  (os.path.join(('./Task/%s' % taskId), xmlScript),
                   serverIp, localPort, remoteSock, request.data.get('beginConcurrentNum'),)
                   #    int(request.data.get('lastForCallTime'))*int(request.data.get('beginConcurrentNum')))
        # 拷贝csv文件
        if request.data.get('csvScript'):
            shutil.copy(os.path.join(request.data.get('dirPath'), request.data.get('csvScript')),
                        './Task/%s' % taskId)
            sippCmd += " -inf %s" % os.path.join('./Task/%s' % taskId, request.data.get('csvScript'))
        # 判断有没有丢包率
        if request.data.get('lostRate'):
            sippCmd += " -lost %s" % request.data.get('lostRate')
        sippCmd += " -ci 127.0.0.1 -trace_screen -trace_err -bg"
        #print(sippCmd)

        # 判断呼叫类型
        if request.data.get('callType') == "1":
            sippCmd += " -m %d" % (int(request.data.get('lastForCallTime'))*int(request.data.get('beginConcurrentNum')))
            timeOptions = 0
        else:
            timeOptions = 1
        print(sippCmd)
        stdOut = subprocess.getstatusoutput(sippCmd)    # 执行sipp命令，开启任务
        # send = subprocess.Popen(sippCmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        time.sleep(0.1)
        startTime = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")    # 获取当前时间作为任务开始时间  + datetime.timedelta(hours=8)
        print(startTime)
        # rint(send.communicate())
        #   stdOut = send.stdout.readlines()
        # send.stdin.close()
        if "No injection file was specified" in stdOut[1]:
            return Response({'code': 10004, 'error': '当前执行的xml脚本需要引入csv文件'})
        elif "Unable to bind main socket" in stdOut[1]:
            return Response({'code': 10005, 'error': '无法绑定本地udp端口，请切换端口'})
        elif "PID=[" in stdOut[1]:
            pid = int(stdOut[1].split("PID=[")[1][:-1])
            print(pid)
        else:
            return Response({'code': 10006, 'error': stdOut[1]})
        #time.sleep(0.01)
        stdOut = subprocess.getstatusoutput("sudo lsof -i udp -P|grep -w %s|tail -n 1|awk -F':' '{print $NF}'" % pid)  # 这一句要优化，太慢
        if stdOut[0] == 0:
            print(stdOut)
            if int(stdOut[1]) >= 8888:
                localControlPort = stdOut[1]
                print('Local_control_port', localControlPort)
                print(type(taskId), type(user), type(pid), type(localControlPort))
                tbl_task.objects.create(taskId=taskId, user=user, pid=pid, localControlPort=localControlPort,
                                        startTime=startTime, taskStatus=1, timeOptions=timeOptions, **request.data)
                # 更新sip配置表的状态字段为正在使用
                tbl_sipcfg.objects.filter(user=user, localPort=localPort).update(isRunning=True)
                tbl_sys.objects.filter(pk=1).update(
                    currentConNum=currentConNum + request.data.get('beginConcurrentNum'))
                ret = {'code': 10000, 'data': request.data, 'error': None}
                return Response(ret)
        else:
            print(stdOut)
            subprocess.getstatusoutput('kill -9 %s' % pid)
            return Response({'code': 10007, 'error': '任务创建失败'})

    def stopTask(self, request):
        print(request.data)
        user = User.objects.filter(username='admin').first()
        taskObj = tbl_task.objects.filter(user=user, taskName=request.data.get('id')).first()
        if taskObj:
            #stdOut = subprocess.getstatusoutput("sudo kill -USR1 %s" % taskObj.pid)
            stdOut = subprocess.getstatusoutput("sudo kill -9 %s" % taskObj.pid)
            #endTime = str(datetime.datetime.now() + datetime.timedelta(hours=8)).split(".")[0]
            print(stdOut)
            if stdOut[0] == 0:
                # 写入任务的结束时间
                #tbl_task.objects.filter(user=user, taskName=request.data.get('taskName')).update(endTime=endTime)
                # 将sip路由表的状态更新为未使用状态
                #tbl_sipcfg.objects.filter(user=user, localPort=taskObj.callRoute.split('<==>')[0]).update(isRunning=False)
                # 将系统表的当前并发数更新
                #tbl_sys.objects.filter(pk=1).update(currentConNum=F('currentConNum')-taskObj.beginConcurrentNum)
                return Response({'code': 10000, 'error': None})
            else:
                return Response({'code': 10002, 'error': stdOut[1]})
        return Response({'code': 10001, 'error': '任务不存在'})

    def handleTask(self, request):
        action = request.data.get('action')
        id = request.data.get('id')
        print(id)
        if action == "pause" or "play":
            try:
                localControlPort = tbl_task.objects.filter(id=id, taskStatus=1).first().localControlPort
                outPut = subprocess.getstatusoutput("sudo echo 'p'> /dev/udp/127.0.0.1/%s" % localControlPort)
                if outPut[0] == 0:
                    return Response({'code': 10000, 'error': None})
            except Exception:
                return Response({'code': 10001, 'error': "任务已结束，操作失败！"})
        elif action == "stop":
            try:
                pid = tbl_task.objects.filter(id=id, taskStatus=1).first().pid
                outPut = subprocess.getstatusoutput("sudo kill -9 %s" % pid)
                if outPut[0] == 0:
                    return Response({'code': 10000, 'error': None})
            except Exception:
                return Response({'code': 10001, 'error': "任务已结束，操作失败！"})
        else:
            return Response({'code': 10002, 'error': "操作失败"})

    def getTaskList(self, request):
        username = request.username
        user = User.objects.filter(username=username).first()
        taskObj = list(tbl_task.objects.filter(user=user).all().values('id', 'taskStatus', 'taskName', 'taskId'))
        taskObj.reverse()
        data = {}
        for item in taskObj:
            if data.get(item['taskStatus']):
                data.get(item['taskStatus']).append({"id": item['id'], "taskName": item['taskName'], 'taskId': item['taskId']})
            else:
                data[item['taskStatus']] = [{"id": item['id'], "taskName": item['taskName'], 'taskId': item['taskId']}]
        return Response({'code': 10000, 'data': data, 'error': None})

    def computeTime(self, strTime):
        tmp_li = strTime.split(":")
        count = int(tmp_li[0])*3600 + int(tmp_li[1])*60 + int(tmp_li[2])
        #   print(count)
        return count

    def getTaskInfo(self, request):
        username = request.username
        user = User.objects.filter(username=username).first()
        try:
            if request.data.get('id'):
                taskInfoObj = tbl_task.objects.filter(id=request.data.get('id')).values()[0]
                print(taskInfoObj)
            else:
                taskInfoObj = list(tbl_task.objects.filter(user=user).values())[-1]   # 不支持负索引
                print(taskInfoObj)
            completionRate = round(self.computeTime(taskInfoObj['elapsedTime']) / (
                self.computeTime(taskInfoObj['callLength']) + taskInfoObj['lastForCallTime']) * 100, 2)
            #   print(completionRate)
            surplusTime = (self.computeTime(taskInfoObj['callLength']) + taskInfoObj['lastForCallTime']) - self.computeTime(taskInfoObj['elapsedTime'])
            taskInfoObj['completionRate'] = completionRate  # 任务完成率
            taskInfoObj['surplusTime'] = surplusTime
            statObj = tbl_stat.objects.filter(taskPk_id=taskInfoObj['id']).last()
            taskInfoObj['responseTime'] = statObj.responseTime
            taskInfoObj['currentCallNum'] = statObj.currentCallNum
            taskInfoObj['avgCallLength'] = statObj.avgCallLength
            taskInfoObj['asr'] = statObj.asr
            taskInfoObj['callRate'] = statObj.callRate
        except Exception as e:
            print(e)
            taskInfoObj = {}

        return Response({'code': 10000, 'data': taskInfoObj, 'error': None})

    def delTask(self, request):
        taskId = request.data.get('taskId')
        print("id", taskId)
        tbl_stat.objects.filter(taskPk__taskId=taskId).delete()
        tbl_task.objects.filter(taskId=taskId).delete()
        shutil.rmtree('./Task/%s' % taskId)
        return Response(None)
