#from rest_framework import serializers
from sippv2 import settings

from .models import *
import os, time
import configparser
"""
class SippSerialize(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")
    pathname = serializers.CharField()
    #filename = serializers.CharField(source="files.filename")
    pid = serializers.CharField(source="resource.pid")

    class Meta:
        model = resource
        fields = ('id', "pathname")
"""


"""递归查询目录函数"""
def list_dir(rootPath):
    # rootpath: "./Script"; 'aaaa'.split("/")[:-1]不会报错返回[]
    tmp_li = []
    # res = {"pathName": rootPath.split("/")[-1], "nodes": [], "tags": 0, "parent": rootPath.split("./")[1].split("/")}
    res = {"pathName": rootPath.split("/")[-1], "nodes": [], "tags": 0, "path": os.getcwd()+rootPath[1:]}
    dir_tmp = os.listdir(rootPath)
    for i in dir_tmp:
        if os.path.isfile(rootPath + "/" + i):
            res["tags"] += 1
        else:

            """if mainpath == rootPath.split("/")[-1]:
                
                res["state"] = {"expanded": True, "checked": True, "selected": True}
            else:
                res['state'] = {'expanded': True, "checked": False, "selected": False}
            """
            tmp_li.append(i)
    if tmp_li:

        for a in tmp_li:
            res["nodes"].append(list_dir(rootPath+"/"+a))
    return res


"""时间格式化函数"""
def timeSerialize(times):
    timeStamp = time.localtime(times)
    return time.strftime("%Y-%m-%d %H:%M:%S", timeStamp)


"""根据类型查询文件数量"""
def getFilesInfo(request):
    # dirPath = os.getcwd() + "/" + "/".join(request.data.get('dirPath', ''))
    dirPath = request.data.get('dirPath')
    #   print(request.data.get('dirPath'))
    fileType, offset, limit = request.data.get("type"), request.data.get('offset'), request.data.get('limit')
    if not (fileType in ["xml", "csv", "pcap"]):
        fileType = ["xml", "csv", "pcap"]
    search = request.data.get('search', '')
    print(dirPath, fileType)
    tmp_li = os.listdir(dirPath)
    file_list = []
    for i in tmp_li:
        print(i)
        if (i.split(".")[-1] in fileType) and (search in i):
            fileInfo = os.stat(os.path.join(dirPath, i))
            CreateTime, ModifyTime, Size = fileInfo.st_atime, fileInfo.st_mtime, str(fileInfo.st_size) + "kb"
            file_dict = {"fileName": i, "CreateTime": timeSerialize(CreateTime), "ModifyTime": timeSerialize(ModifyTime), "Size": Size}
            file_list.append(file_dict)
    total = len(file_list)
    # return {"total": total, "list": file_list[offset: offset + limit], "CurrentPath": dirPath}
    if limit:
        return {"total": total, "list": file_list[offset: offset + limit]}
    else:
        return {"total": total, "list": file_list}


def readingConfig(configFileNmae):
    """读取配置文件，返回配置字段"""
    obj = configparser.ConfigParser()
    obj.read(os.path.join(settings.BASE_DIR, configFileNmae))
    serverIp = obj.get('config', 'serverIp')
    localStartSipPort = obj.get('config', 'localStartSipPort')
    usablePortCount = obj.get('config', 'usablePortCount')
    concurrencyNum = obj.get('config', 'concurrencyNum')
    return serverIp, localStartSipPort, usablePortCount, concurrencyNum

def writingConfig(configFileNane, serverIp, localStartSipPort, usablePortCount, concurrencyNum):
    """重写配置文件"""
    print(configFileNane, serverIp, localStartSipPort, usablePortCount, concurrencyNum)
    obj = configparser.ConfigParser()
    obj.read(os.path.join(settings.BASE_DIR, configFileNane))
    obj.sections()
    obj.set('config', 'serverIp', serverIp)
    obj.set('config', 'localStartSipPort', localStartSipPort)
    obj.set('config', 'usablePortCount', usablePortCount)
    obj.set('config', 'concurrencyNum', concurrencyNum)
    with open(os.path.join(settings.BASE_DIR, configFileNane), 'w') as f:
       #print(type(f))
        obj.write(f)    # 这里是obj对象调用自己的write 方法将配置写入文件
    return 1


serverIp, localStartSipPort, usablePortCount, concurrencyNum = readingConfig("config.ini")
print(serverIp, localStartSipPort, usablePortCount, concurrencyNum)


def init():
    obj = tbl_sipcfg.objects.all().values_list('localPort')  # 查询已使用的本地sip端口
    port_list = []
    usablePortList = ''
    for item in obj:
        port_list.append(int(item[0]))
    print(port_list)
    for port in range(int(usablePortCount)):
        if int(localStartSipPort) + port in port_list:
            continue
        usablePortList += str((int(localStartSipPort) + port)) + ","
    print(usablePortList)
    #tbl_sys.objects.filter(pk=1).update(port_list=usablePortList)
    return usablePortList
