from django.db import models

# Create your models here.


class User(models.Model):
    username = models.CharField(max_length=16, null=False, verbose_name="用户名")
    password = models.CharField(max_length=32, null=False, verbose_name="密码")

    def __str__(self):
        return self.username


class Token(models.Model):
    user = models.OneToOneField('User', on_delete=models.CASCADE, null=False)
    uuid = models.UUIDField(null=False)


class tbl_sys(models.Model):
    """status_choice = (
        (0, "-"),
        (1, "up"),
        (2, "down")
    )"""
    currCpu = models.FloatField(max_length=8, null=False, verbose_name="当前cpu使用率", default=0)
    #cpu_status = models.IntegerField(choices=status_choice, null=False, verbose_name="cpu状态", default=0)
    #cpu_rate = models.FloatField(max_length=8, null=False, verbose_name="cpu状态", default=0)

    currMem = models.FloatField(max_length=8, null=False, verbose_name="当前Mem使用率", default=0)
    #mem_status = models.IntegerField(choices=status_choice, null=False, verbose_name="cpu状态", default=0)
    #mem_rate = models.FloatField(max_length=8, null=False, verbose_name="cpu状态", default=0)

    currDisk = models.FloatField(max_length=8, null=False, verbose_name="当前disk使用率", default=0)
    #disk_status = models.IntegerField(choices=status_choice, null=False, verbose_name="cpu状态", default=0)
    #disk_rate = models.FloatField(max_length=8, null=False, verbose_name="cpu状态", default=0)

    curr_rx = models.FloatField(max_length=8, null=False, verbose_name="当前接收流量", default=0)
    #rx_status = models.IntegerField(choices=status_choice, null=False, verbose_name="上行流量趋势率", default=0)
    #rx_rate = models.FloatField(max_length=8, null=False, verbose_name="上行流量趋势率", default=0)


    #   rx_last_difference = models.IntegerField(max_length=16, null=False, verbose_name="上次上行流量的差值", default=0)
    curr_tx = models.FloatField(max_length=8, null=False, verbose_name="当前下行流量", default=0)
    #tx_status = models.IntegerField(choices=status_choice, null=False, verbose_name="趋势状态", default=0)
    #tx_rate = models.FloatField(max_length=8, null=False, verbose_name="下行流量趋势率", default=0)
    #   tx_last_difference = models.IntegerField(max_length=16, null=False, verbose_name="上次下行流量的差值", default=0)
    port_list = models.CharField(max_length=1024, null=True, verbose_name="sip端口可用列表")
    currentConNum = models.IntegerField(null=False, default=0, verbose_name="系统当前总呼叫并发数")
    currentCps = models.FloatField(null=False, default=0, verbose_name="当前系统总的cps")
    sysTime = models.CharField(max_length=19, null=True, verbose_name="数据生成时间")

class tbl_sipcfg(models.Model):
    localPort = models.CharField(max_length=8, null=False, verbose_name="本端sipp端口")
    remoteAddr = models.GenericIPAddressField(max_length=32, null=False, verbose_name="对端sip地址")
    remotePort = models.CharField(max_length=8, null=False, verbose_name="对端sip端口")
    user = models.ForeignKey('user', on_delete=models.CASCADE, verbose_name="关联用户")
    isRunning = models.BooleanField(default=False, verbose_name="正在使用标志位")


class tbl_task(models.Model):
    taskId = models.IntegerField(unique=True, verbose_name="任务id", default=1)
    user = models.ForeignKey('user', null=False, on_delete=models.CASCADE)
    taskName = models.CharField(max_length=16, null=False, verbose_name="任务名称")
    pid = models.IntegerField(null=False, verbose_name="任务进程id")
    localControlPort = models.IntegerField(null=True, verbose_name="本地远程控制端口")
    callType = models.IntegerField(null=True, verbose_name="呼叫类型")
    startTime = models.CharField(max_length=19, null=True, verbose_name="任务创建时间")
    callRoute = models.CharField(max_length=32, null=True, verbose_name="呼叫路由")
    xmlScript = models.CharField(max_length=32, null=True, verbose_name="xml脚本名称")
    csvScript = models.CharField(max_length=32, null=True, verbose_name="csv脚本名称")
    beginConcurrentNum = models.IntegerField(null=True, verbose_name="初始呼叫并发数")
    lostRate = models.IntegerField(null=True, verbose_name="丢包率")
    lastForCallTime = models.IntegerField(null=True, verbose_name="呼叫时长")
    timeOptions = models.IntegerField(null=False, default=0, verbose_name="呼叫执行阶段，恒并对，递增，递减")
    increaseTime = models.CharField(max_length=32, null=True, verbose_name="开始递增时间")
    increaseConNum = models.IntegerField(null=True, verbose_name="递增并发数")
    decreaseTime = models.CharField(max_length=32, null=True, verbose_name="开始递减时间")
    decreaseConNum = models.IntegerField(null=True, verbose_name="递减并发数")
    dirPath = models.CharField(max_length=128, null=True, verbose_name="脚本所在目录")
    taskStatus = models.IntegerField(null=False, default=0, verbose_name="任务状态")
    qFlag = models.BooleanField(default=False, verbose_name="是否发送过q的标志位")
    elapsedTime = models.CharField(max_length=8, null=True, verbose_name="当前任务已呼叫时长")
    callRate = models.CharField(max_length=12, null=True, verbose_name="当前任务cps")   # 这个当前cps可以不要
    totalCallCreatedNum = models.IntegerField(null=True, verbose_name="当前任务已呼叫总数")
    #currentCall = models.IntegerField(null=True, verbose_name="当前任务呼叫数")
    successfulCallNum = models.IntegerField(null=True, verbose_name="当前任务呼叫成功数")
    failedCallNum = models.IntegerField(null=True, verbose_name="当前任务呼叫失败数")
    msgLog = models.TextField(null=True, verbose_name="消息日志字符串")
    errorReason = models.TextField(null=True, verbose_name="失败原因字符串")
    callLength = models.CharField(max_length=8, null=True, verbose_name="总通话时长")
    endTime = models.CharField(max_length=19, null=True, verbose_name="任务结束时间")


class tbl_stat(models.Model):
    taskPk = models.ForeignKey('tbl_task', on_delete=models.CASCADE, verbose_name="task标识")
    responseTime = models.IntegerField(null=True, verbose_name="响应时间")
    currentCallNum = models.IntegerField(null=False, default=0, verbose_name="当前呼叫数")
    avgCallLength = models.CharField(max_length=8, null=True, verbose_name="平均通话时长")
    asr = models.FloatField(null=True, verbose_name="接通率，access success ratio")
    #   cpuRate = models.FloatField(max_length=8, null=True, default=0, verbose_name="cpu利用率")
    callRate = models.FloatField(null=False, default=0, verbose_name="当前任务cps")
    countTime = models.CharField(max_length=19, null=True, verbose_name="数据生成时间")


class files(models.Model):
    choices = (
        (0, "xml"),
        (1, "csv"),
        (2, "pcap")
    )
    filename = models.CharField(max_length=32, verbose_name='文件名')
    filesize = models.CharField(max_length=8, verbose_name='文件大小')
    filetype = models.IntegerField(choices=choices, verbose_name="文件类型")


class resource(models.Model):
    user = models.ForeignKey('user', null=False, on_delete=models.CASCADE, verbose_name="关联用户id")
    pathname = models.CharField(max_length=32, null=True, verbose_name="路径名")
    #   filename = models.ForeignKey('files', on_delete=models.CASCADE, verbose_name='文件名id')
    pid = models.ForeignKey('self', null=True, on_delete=models.CASCADE, verbose_name='父级id', related_name='subs')

    class Meta:
        unique_together = ('user', 'pathname', 'pid')




