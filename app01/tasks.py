import platform
import psutil
import os
import app01.models
from celery import shared_task
import subprocess
import datetime, time
import json
from app01.serialize import init, serverIp

def getNIC(ipaddr):
    for k, v in psutil.net_if_addrs().items():
        if v[0].address == ipaddr:
            print(k)
            return k


def getSystemVersion():
    SysInfoList = platform.uname()
    systemVersion = SysInfoList[0] + " " + SysInfoList[2] + SysInfoList[4] + " " + SysInfoList[5]
    return systemVersion


a = getSystemVersion()
print(a)


# 获取cpu利用率
def getCurrCpu():
    currCpu = psutil.cpu_percent()  # 当前cpu使用率， 可以传interval=10 获取10秒内平均cpu
    return currCpu


# 获取内存使用率
def getCurrMem():
    currMem = psutil.virtual_memory()[2]
    return currMem


# 获取磁盘利用率
def getDisk():
    total, used = 0, 0
    for i in psutil.disk_partitions():
        total += psutil.disk_usage(i.mountpoint)[0]
        used += psutil.disk_usage(i.mountpoint)[1]
    return round(used / total, 3) * 100


# 呼叫递增或递减方法
def setCallDecreaseOrIncrease(num, port):
    #   subprocess.getstatusoutput("sudo echo 'cset limit %s'> /dev/udp/127.0.0.1/%s" % (num, port))
    subprocess.getstatusoutput(
        "sudo echo 'cset rate %s'> /dev/udp/127.0.0.1/%s" % (num, port))


# 获取系统状态，写进数据库;此方法被优化掉了
# @shared_task
def setSysInfo():
    rx_recv_before, tx_send_before = psutil.net_io_counters(pernic=True)["lo0"][:2]
    #   print(rx_recv_before, tx_send_before)
    import time
    time.sleep(1)
    rx_recv_after, tx_send_after = psutil.net_io_counters(pernic=True)["lo0"][:2]
    #   print(rx_recv_after, tx_send_after)

    # data = app01.models.tbl_sys.objects.all().values()[0]
    #   print(data)
    currCpu = getCurrCpu()
    currMem = getCurrMem()
    currDisk = getDisk()
    curr_rx = (rx_recv_after - rx_recv_before)/1024  # 最少是1024
    curr_tx = (tx_send_after - tx_send_before)/1024
    """
    cpu_last = data.get('currCpu')
    mem_last = data.get('currMem')
    disk_last = data.get('currDisk')
    cpu_rate = round((currCpu - cpu_last), 3)
    mem_rate = round((currMem - mem_last), 3)
    disk_rate = round((currDisk - disk_last), 3)
    rx_last = data.get('curr_rx')
    tx_last = data.get('curr_tx')
       print(type(rx_last), tx_last)
    rx_rate = round((curr_rx - rx_last), 3)
    tx_rate = round((curr_tx - tx_last), 3)
    """
    app01.models.tbl_sys.objects.update_or_create(currCpu=currCpu,
                                                  currMem=currMem,
                                                  currDisk=currDisk,
                                                  curr_rx=curr_rx,
                                                  curr_tx=curr_tx, )


@shared_task
def taskStatusCheck():
    taskList = app01.models.tbl_task.objects.filter(taskStatus=1, qFlag=False).all().values()
    #   print("这是taskList", taskList)
    if taskList:
        qFlagList = []
        for task in taskList:

            """
            updateTaskList = []
            pid = task['pid']
            output = subprocess.getstatusoutput("lsof -i -P|grep %s" % pid)
            if output[0] != 0:  # 说明任务结束了，要更新
                updateTaskList.append(pid)
            elif output[1].split()[0] != "sipp":    # 有这个进程， 但是不是sipp，那也说明任务结束了
                updateTaskList.append(pid)
            """

            # 查看该任务是否到了执行结束时间
            nowTime = int(time.time()) + datetime.timedelta(hours=8).seconds
            startTime = int(time.mktime(time.strptime(task.get('startTime'), "%Y-%m-%d %H:%M:%S")))
            #   print("这是now: %s, 这是start+last: %s" % (nowTime, startTime + task.get('lastForCallTime')))
            if nowTime >= startTime + task.get('lastForCallTime'):
                output = subprocess.getstatusoutput("sudo kill -USR1 %s" % task["pid"])
                if output[0] == 0:
                    print('任务停止成功')
                    qFlagList.append(task['id'])
                else:
                    print('任务停止失败')
            elif task['timeOptions'] in [1, 2]:
                # 这里数据库里存的时间为'2017-07-12 10:05:49' 字符串
                decreaseTime, increaseTime, decreaseConNum, increaseConNum, localControlPort = \
                    task['decreaseTime'], task['increaseTime'], task['decreaseConNum'], task['increaseConNum'], task[
                        'localControlPort']
                # 将日期字符串转化为秒级时间戳，如果没有返回None

                decreaseTime, increaseTime = map(
                    lambda x: int(time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S"))) if x else None,
                    [decreaseTime, increaseTime])
                #   print("时间：", decreaseTime, increaseTime)
                if task.get('timeOptions') == 1:
                    #   print("test111111111")
                    if decreaseTime and nowTime >= decreaseTime and not increaseTime:
                        """
                        subprocess.getstatusoutput("echo 'cset limit %s'> /dev/udp/127.0.0.1/%s" % (decreaseConNum, localControlPort))
                        subprocess.getstatusoutput(
                            "echo 'cset rate %s'> /dev/udp/127.0.0.1/%s" % (decreaseConNum, localControlPort))
                        """
                        setCallDecreaseOrIncrease(decreaseConNum, localControlPort)
                        app01.models.tbl_task.objects.filter(id=task['id']).update(timeOptions=3)

                    elif increaseTime and nowTime >= increaseTime and not decreaseTime:
                        # 设置递增
                        #   print("test22222")
                        setCallDecreaseOrIncrease(increaseConNum, localControlPort)
                        app01.models.tbl_task.objects.filter(id=task['id']).update(timeOptions=3)

                    elif decreaseTime and increaseTime:
                        if decreaseTime <= nowTime <= increaseTime:
                            # 递减
                            setCallDecreaseOrIncrease(decreaseConNum, localControlPort)
                            app01.models.tbl_task.objects.filter(id=task['id']).update(timeOptions=2)

                        elif increaseTime <= nowTime <= decreaseTime:
                            # 设置递增
                            setCallDecreaseOrIncrease(increaseConNum, localControlPort)
                            app01.models.tbl_task.objects.filter(id=task['id']).update(timeOptions=2)

                if task.get('timeOptions') == 2:
                    if decreaseTime < increaseTime <= nowTime:
                        # 设置递增
                        setCallDecreaseOrIncrease(increaseConNum, localControlPort)
                        app01.models.tbl_task.objects.filter(id=task['id']).update(timeOptions=3)
                    elif increaseTime < decreaseTime <= nowTime:
                        # 设置递减
                        setCallDecreaseOrIncrease(decreaseConNum, localControlPort)
                        app01.models.tbl_task.objects.filter(id=task['id']).update(timeOptions=3)

            else:
                pass
        if qFlagList:
            app01.models.tbl_task.objects.filter(pk__in=qFlagList).update(qFlag=True)


@shared_task
# 实时更新任务状态信息
def updateTaskStatInfo():
    taskList = app01.models.tbl_task.objects.filter(taskStatus=1).values("id", "pid", "taskId", "xmlScript",
                                                                         "callRoute")
    currentConNum = 0
    currentCps = 0
    if taskList:
        # 重新计算当前总并发数

        updateTaskList = []
        for item in list(taskList):
            pid = item['pid']
            #   print(pid)
            if not psutil.pid_exists(pid) or psutil.Process(pid=pid).name() != "sipp":
                if not updateTaskList:
                    updateTaskList.append([item['id']])
                    updateTaskList.append([item['callRoute'].split('<==>')[0]])
                else:
                    updateTaskList[0].append(item['id'])
                    updateTaskList[1].append(item['callRoute'].split('<==>')[0])

            subprocess.getstatusoutput("sudo kill -USR2 %s" % pid)
            print("发送信号")  # 少了最后一次的统计
        for item in list(taskList):
            with open(os.path.join('./Task', str(item['taskId']),
                                   "%s_%s_screen.log" % (item['xmlScript'][:-4], item['pid'] - 1)), "r") as f:
                # 将文件读取指针移动到相对与文件末尾(2), 0个字节
                msg = f.readlines()[-68:]
            print("这是消息日志", msg)
            TimeStatPosition = msg.index(
                "----------------------------- Statistics Screen ------- [1-9]: Change Screen --\n")
            # 消息日志界面开始位置
            try:
                msgLogStartPosition = msg.index(
                    "                                 Messages  Retrans   Timeout   Unexpected-Msg\n")
            except Exception as e:
                msgLogStartPosition = msg.index(
                    "                                 Messages  Retrans   Timeout   Unexp.    Lost\n")
            # 根据任务正在执行或任务结束的不同字符串，获取消息日志的界面结束位置
            if "------ [+|-|*|/]: Adjust rate ---- [q]: Soft exit ---- [p]: Pause traffic -----\n" in msg:
                msgLogEndPosition = msg.index(
                    "------ [+|-|*|/]: Adjust rate ---- [q]: Soft exit ---- [p]: Pause traffic -----\n")
            elif "------- Waiting for active calls to end. Press [q] again to force exit. -------\n" in msg:
                msgLogEndPosition = msg.index(
                    "------- Waiting for active calls to end. Press [q] again to force exit. -------\n")
            else:
                msgLogEndPosition = msg.index(
                    "------------------------------ Sipp Server Mode -------------------------------\n")
            # 计数器界面位置
            CounterPositon = msg.index(
                "  Counter Name           | Periodic value            | Cumulative value\n")
            # Start Time 开始时间
            startTime = msg[TimeStatPosition + 1].split()[3] + " " + \
                        msg[TimeStatPosition + 1].split()[4].split(".")[0]
            startTime = (datetime.datetime.strptime(startTime, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
            # Elapsed Time 已呼叫时间
            elapsedTime = msg[CounterPositon + 2].split()[5][:8]
            # Call Rate 呼叫频率
            callRate = float(msg[CounterPositon + 3].split()[6])
            # Total Call created	总呼叫数
            totalCallCreatedNum = int(msg[CounterPositon + 7].split()[5])
            # Current Call 当前呼叫数
            currentCallNum = int(msg[CounterPositon + 8].split()[3])
            # Successful call 呼叫成功数
            successfulCallNum = int(msg[CounterPositon + 10].split()[5])
            # Failed call 呼叫失败数
            failedCallNum = int(msg[CounterPositon + 11].split()[5])

            if msg[CounterPositon + 13].split()[0] == "Response":
                # Response Time
                responseTime = msg[CounterPositon + 13].split()[6]
                #   print("响应时间是多少", msg[CounterPositon + 13].split()[6])
                responseTimeList = list(map(lambda x: int(x), responseTime.split(":")))  # map对象不支持索引，所以要转换成list
                # 转化成微秒
                responseTime = responseTimeList[0] * 3600000000 + responseTimeList[1] * 60000000 + responseTimeList[
                    2] * 000000 + responseTimeList[3]
                # Call Length 通话时长
                callLength = msg[CounterPositon + 14].split()[5]
                #   print("这是第一次")
                callLengthList = list(map(lambda x: int(x), callLength.split(":")))
                # 转化成微秒
                callLengthSecond = callLengthList[0] * 3600 + callLengthList[1] * 60 + callLengthList[2]

                if int(totalCallCreatedNum) == 0:
                    avgCallLength = 0
                else:
                    avgCallLength = round(callLengthSecond / totalCallCreatedNum, 2)

            else:
                responseTime = 0
                # Call Length 通话时长
                callLength = msg[CounterPositon + 13].split()[5]
                #   print("这是第二次")
                callLengthList = list(map(lambda x: int(x), callLength.split(":")))
                callLengthSecond = callLengthList[0] * 3600 + callLengthList[1] * 60 + callLengthList[2]
                # 平均通话时长
                if int(totalCallCreatedNum) == 0:
                    avgCallLength = 0
                else:
                    avgCallLength = round(callLengthSecond / totalCallCreatedNum, 2)

            # 接通率
            if int(totalCallCreatedNum) == 0:
                asr = 0
            else:
                #   print("successfulCallNum %s" % successfulCallNum)
                #   print("totalCallCreatedNum %s" % totalCallCreatedNum)
                asr = round(float(successfulCallNum) / float(totalCallCreatedNum) * 100, 2)

            # 消息日志字符串
            msgLog = ""
            for j in range(msgLogStartPosition, msgLogEndPosition):
                msgLog += msg[j]

                # 失败原因
            try:
                with open(os.path.join("./Task", str(item['taskId']),
                                       "%s_%s_errors.log" % (item["xmlScript"][:-4], item["pid"])), "r") as f:
                    errorMsg = f.read()

                ReasonCount = errorMsg.count("Reason")  # count(),统计字符串个数
                ReasonDict = {}
                positionStart = 0
                for k in range(ReasonCount):
                    ReasonStartPosition = errorMsg.find("Reason", positionStart)  # a = 'abcda', a.find('a', 1), 4
                    ReasonEndPosition = errorMsg.find('"\r', ReasonStartPosition)
                    ReasonName = errorMsg[ReasonStartPosition:ReasonEndPosition].split('text="')[1]
                    # print "ReasonName: ",ReasonName
                    if ReasonDict.get(ReasonName):
                        ReasonDict[ReasonName] = ReasonDict[ReasonName] + 1
                    else:
                        ReasonDict[ReasonName] = 1
                    positionStart = ReasonEndPosition + 6
            except Exception as e:
                ReasonDict = {}
                print(e)

            print("这是update列表 %s" % updateTaskList)
            if updateTaskList and item['id'] in updateTaskList[0]:
                #   print("这是callLength %s" % callLength[:8])
                endTime = msg[TimeStatPosition + 3].split()[3] + " " + msg[TimeStatPosition + 3].split()[4].split(".")[
                    0]
                endTime = (datetime.datetime.strptime(endTime, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                app01.models.tbl_task.objects.filter(id=item['id']). \
                    update(startTime=startTime, elapsedTime=elapsedTime, callRate=callRate,
                           totalCallCreatedNum=totalCallCreatedNum,
                           successfulCallNum=successfulCallNum, failedCallNum=failedCallNum, msgLog=msgLog,
                           errorReason=json.dumps(ReasonDict), callLength=callLength[:8], endTime=endTime, taskStatus=0)
                # localPort = item['callRoute'].split('<==>')[0]
                # app01.models.tbl_sipcfg.objects.filter(localPort=int(localPort)).update(isRunning=False)
                # 要不要把最大并发数更新
            else:
                app01.models.tbl_task.objects.filter(id=item['id']). \
                    update(startTime=startTime, elapsedTime=elapsedTime, callRate=callRate,
                           totalCallCreatedNum=totalCallCreatedNum,
                           successfulCallNum=successfulCallNum, failedCallNum=failedCallNum, msgLog=msgLog,
                           errorReason=json.dumps(ReasonDict), callLength=callLength[:8])
            countTime = str(datetime.datetime.now() + datetime.timedelta(hours=8)).split(".")[0]
            app01.models.tbl_stat.objects.create(taskPk_id=item['id'], responseTime=responseTime,
                                                 currentCallNum=currentCallNum, avgCallLength=avgCallLength, asr=asr,
                                                 callRate=callRate, countTime=countTime)
            currentConNum += currentCallNum
            currentCps += int(callRate)
        # 将完成任务的路由状态更新
        if updateTaskList:
            #   localPortList = map(lambda x: list(x.values())[0], updateTaskList)  # 注意，通过.values()得到的是dict_values类型， 要用list()方法转化才能index
            #   print("这是localPortList %s" % updateTaskList[1])
            app01.models.tbl_sipcfg.objects.filter(localPort__in=updateTaskList[1]).update(isRunning=False)

    else:
        pass
    NIC = getNIC(serverIp)
    rx_recv_before, tx_send_before = psutil.net_io_counters(pernic=True)[NIC][:2]
    #   print(rx_recv_before, tx_send_before)
    import time
    time.sleep(1)
    rx_recv_after, tx_send_after = psutil.net_io_counters(pernic=True)[NIC][:2]
    #   print(rx_recv_after, tx_send_after)

    # data = app01.models.tbl_sys.objects.all().values()[0]
    #   print(data)
    currCpu = getCurrCpu()
    currMem = getCurrMem()
    currDisk = getDisk()
    curr_rx = (rx_recv_after - rx_recv_before)/1024  # 最少是1024
    curr_tx = (tx_send_after - tx_send_before)/1024
    sysTime = str(datetime.datetime.now() + datetime.timedelta(hours=8)).split(".")[0].replace("-", "/")
    port_list = init()
    app01.models.tbl_sys.objects.update_or_create(currCpu=currCpu,
                                                  currMem=currMem,
                                                  currDisk=currDisk,
                                                  curr_rx=curr_rx,
                                                  curr_tx=curr_tx,
                                                  currentConNum=currentConNum,
                                                  currentCps=currentCps,
                                                  port_list=port_list,
                                                  sysTime=sysTime)
    num = app01.models.tbl_sys.objects.count()
    if num > 300:
        app01.models.tbl_sys.objects.first().delete()
