import json
import time
import datetime
from dateutil import tz
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import CreateScheduledTaskRequest

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkecs.request.v20140526 import (
    CreateInstanceRequest,
    AllocatePublicIpAddressRequest,
    StartInstanceRequest,
    DescribeInstancesRequest,
    ModifyInstanceAutoReleaseTimeRequest,
)

# 配置访问密钥和密钥ID
ACCESS_KEY_ID = "LTAI5t77RHozE1RjuHt3Duxd"
ACCESS_SECRET = "m5lCvhHQTU9epnrRdDiUCcsDMSSZlg"

# 设置地区
region_id = "cn-zhangjiakou"

# 初始化客户端
client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, region_id)

# 配置实例参数
instance_type = "ecs.se1.large"
security_group_id = "sg-8vbdminvtx8jh306o18u"
vswitch_id = "vsw-8vbi4ohmz5c1nsoasmnkl"
image_ids = [
    "m-8vben2f0ysfmjq3ti6xz", "m-8vb7rdiuu3e6ctc2he6t",
    "m-8vbhjx185w94owpeci1x"
]

# 镜像和实例名称对应关系
image_to_instance_name_map = {
    "m-8vben2f0ysfmjq3ti6xz": "hadoop102",
    "m-8vb7rdiuu3e6ctc2he6t": "hadoop103",
    "m-8vbhjx185w94owpeci1x": "hadoop104"
}

# 内网地址和实例对应关系
image_to_private_ip_map = {
    "m-8vben2f0ysfmjq3ti6xz": "172.29.16.12",
    "m-8vb7rdiuu3e6ctc2he6t": "172.29.16.13",
    "m-8vbhjx185w94owpeci1x": "172.29.16.14"
}

# 收集实例，为释放做准备
created_instance_ids = []

# 确保实例正常运行，在进行分配公网等操作，避免出现没有资源的情况。


def wait_instance_running(instance_id_param):
    while True:
        request = DescribeInstancesRequest.DescribeInstancesRequest()
        request.set_InstanceIds(json.dumps([instance_id_param]))
        response = client.do_action_with_exception(request)
        response_json = json.loads(response.decode('utf-8'))
        instance_status = response_json['Instances']['Instance'][0]['Status']
        if instance_status == 'Running':
            break
        time.sleep(5)  # 等待5秒后再次检查实例状态


def create_scheduled_backup_task(instance_id, backup_time):
    try:
        request = CreateScheduledTaskRequest.CreateScheduledTaskRequest()
        request.set_LaunchTime(backup_time)
        request.set_ScheduledAction("CreateImage")
        request.set_TaskEnabled(True)
        request.set_TaskName(
            f"Backup-{instance_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )
        request.set_InstanceIds(json.dumps([instance_id]))
        request.set_ImageName(
            f"Backup-{instance_id}-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        )
        response = client.do_action_with_exception(request)
        response_json = json.loads(response.decode("utf-8"))
        task_id = response_json.get("ScheduledTaskId")
        print(f"定时任务 {task_id} 已成功创建，将在 {backup_time} 为实例 {instance_id} 创建镜像。")
    except ServerException as e:
        print(f"创建定时任务失败，错误信息: {e.error_code} - {e.message}")
    except ClientException as e:
        print(f"创建定时任务失败，错误信息: {e.error_code} - {e.message}")


# 创建实例
for image_id in image_ids:
    request = CreateInstanceRequest.CreateInstanceRequest()
    request.set_InstanceType(instance_type)
    request.set_SecurityGroupId(security_group_id)
    request.set_VSwitchId(vswitch_id)
    request.set_ImageId(image_id)
    request.set_PrivateIpAddress(image_to_private_ip_map[image_id])  # 设置内网IP

    # 付费模式: 抢占式实例
    request.set_InstanceChargeType("PrePaid")
    # 单台实例规格上限价: 使用自动出价
    request.set_SpotStrategy("SpotWithPriceLimit")
    request.set_SpotPriceLimit(1)

    # 实例参数
    request.set_InstanceName(image_to_instance_name_map[image_id])
    request.set_HostName(image_to_instance_name_map[image_id])

    # 存储: 高效云盘，40G
    request.set_SystemDiskCategory("cloud_efficiency")
    request.set_SystemDiskSize(40)

    # 公网IP: 分配ipv4，按使用流量
    request.set_InstanceChargeType("PostPaid")
    request.set_InternetChargeType("PayByTraffic")
    request.set_InternetMaxBandwidthOut(80)  # 带宽峰值为80Mbps

    # 登录凭证: 使用镜像预设密码
    request.set_PasswordInherit(True)

    # 发送创建实例请求
    try:
        response = client.do_action_with_exception(request)
        response_json = json.loads(response.decode("utf-8"))
        instance_id = response_json.get("InstanceId")

        # 将实例ID添加到列表中
        created_instance_ids.append(instance_id)

        # 分配公网IP
        allocate_public_ip_request = AllocatePublicIpAddressRequest.AllocatePublicIpAddressRequest(
        )
        allocate_public_ip_request.set_InstanceId(instance_id)
        allocate_public_ip_response = client.do_action_with_exception(
            allocate_public_ip_request)
        allocate_public_ip_response_json = json.loads(
            allocate_public_ip_response.decode("utf-8"))
        public_ip = allocate_public_ip_response_json.get("IpAddress")

        # 启动实例
        start_instance_request = StartInstanceRequest.StartInstanceRequest()
        start_instance_request.set_InstanceId(instance_id)
        start_instance_response = client.do_action_with_exception(
            start_instance_request)

        # 输出公网IP和主机名
        print(public_ip, image_to_instance_name_map[image_id])

    except ServerException as e:
        print("实例创建失败，错误信息:", e.error_code, "-", e.message)
    except ClientException as e:
        print("实例创建失败，错误信息:", e.error_code, "-", e.message)

for instance_id in created_instance_ids:
    try:
        # 等待实例变为"运行中"状态
        wait_instance_running(instance_id)

        auto_release_time = (
            datetime.datetime.utcnow() +
            datetime.timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%SZ')

        modify_auto_release_time_request = ModifyInstanceAutoReleaseTimeRequest.ModifyInstanceAutoReleaseTimeRequest(
        )

        modify_auto_release_time_request.set_InstanceId(instance_id)
        modify_auto_release_time_request.set_AutoReleaseTime(auto_release_time)
        modify_auto_release_time_response = client.do_action_with_exception(
            modify_auto_release_time_request)

        # 将UTC时间字符串解析为datetime对象
        utc_time = datetime.datetime.strptime(auto_release_time,
                                              '%Y-%m-%dT%H:%M:%SZ')

        # 将UTC时间转换为北京时间
        utc_tz = tz.tzutc()
        beijing_tz = tz.gettz('Asia/Shanghai')
        beijing_time = utc_time.replace(tzinfo=utc_tz).astimezone(beijing_tz)

        # 将北京时间格式化为指定的字符串格式
        beijing_time_str = beijing_time.strftime('%Y年%m月%d日 %H:%M')

        print("实例 ", instance_id, " 自动释放设置成功，释放时间:", beijing_time_str)

        # 计算备份时间
        backup_time = (datetime.datetime.utcnow() + datetime.timedelta(
            hours=2, minutes=50)).strftime('%Y-%m-%dT%H:%M:%SZ')

        # 创建定时任务
        create_scheduled_backup_task(instance_id, backup_time)

    except ServerException as e:
        print("设置自动释放时间失败，错误信息:", e.error_code, "-", e.message)
    except ClientException as e:
        print("设置自动释放时间失败，错误信息:", e.error_code, "-", e.message)
