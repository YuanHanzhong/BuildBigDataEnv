import json
import time
import datetime
from dateutil import tz
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.JoinSecurityGroupRequest import JoinSecurityGroupRequest
import logging

from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkecs.request.v20140526 import (
    CreateInstanceRequest,
    AllocatePublicIpAddressRequest,
    StartInstanceRequest,
    DescribeInstancesRequest,
    ModifyInstanceAutoReleaseTimeRequest,
)
import requests
import re

# 配置实例参数
instance_type = "ecs.se1.large"

# 要加入的安全组列表
security_group_ids = ["sg-8vbdminvtx8jh306o18u", "sg-8vbap91nk99v1ypw280a"]

# security_group_id_all_ip = "sg-8vbdminvtx8jh306o18u"

# security_group_id_all_port = "sg-8vbap91nk99v1ypw280a"

# sg-8vbdminvtx8jh306o18u 对所有 ip 开放10000 22 端口
# sg-8vbap91nk99v1ypw280a 对特定ip开放所有端口

vswitch_id = "vsw-8vbi4ohmz5c1nsoasmnkl"
image_ids = [
    "m-8vben2f0ysfmxp8p86o6",  # hadoop104
    "m-8vbgy1yye4xwlqrj1lm4",  # hadoop103
    "m-8vbccvbehw3dwynsoos8"  # hadoop102
]

# 配置访问密钥和密钥ID
ACCESS_KEY_ID = "LTAI5t77RHozE1RjuHt3Duxd"
ACCESS_SECRET = "m5lCvhHQTU9epnrRdDiUCcsDMSSZlg"

# 设置地区
region_id = "cn-zhangjiakou"

# 初始化客户端
client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, region_id)

# 镜像和实例名称对应关系
image_to_instance_name_map = {
    image_ids[2]: "hadoop102",
    image_ids[1]: "hadoop103",
    image_ids[0]: "hadoop104"
}

# 内网地址和实例对应关系
image_to_private_ip_map = {
    image_ids[2]: "172.29.16.12",
    image_ids[1]: "172.29.16.13",
    image_ids[0]: "172.29.16.14"
}

# 实例列表
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


print("")
print("")

# 创建实例
for image_id in image_ids:
    request = CreateInstanceRequest.CreateInstanceRequest()
    request.set_InstanceType(instance_type)

    if security_group_ids:
        request.set_SecurityGroupId(security_group_ids[0])

    request.set_VSwitchId(vswitch_id)
    request.set_ImageId(image_id)
    request.set_PrivateIpAddress(image_to_private_ip_map[image_id])  # 设置内网IP

    # 付费模式: 抢占式实例
    request.set_InstanceChargeType("PrePaid")
    # 单台实例规格上限价: 使用自动出价
    request.set_SpotStrategy("SpotWithPriceLimit")
    request.set_SpotPriceLimit(1)

    # 禁用删除保护, 但仍然收到短信验证。如果true了，需要额外在控制台设置禁用然后才能删除
    request.set_DeletionProtection("false")

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

        # 将实例添加到其他安全组
        if len(security_group_ids) > 1:
            for sg_id in security_group_ids[1:]:
                join_security_group_request = JoinSecurityGroupRequest()
                join_security_group_request.set_InstanceId(instance_id)
                join_security_group_request.set_SecurityGroupId(sg_id)
                join_security_group_response = client.do_action_with_exception(
                    join_security_group_request)

        # 输出公网IP和主机名
        print(public_ip, image_to_instance_name_map[image_id])

    except ServerException as e:
        print("实例创建失败，错误信息:", e.error_code, "-", e.message)
    except ClientException as e:
        print("实例创建失败，错误信息:", e.error_code, "-", e.message)

# 给实例时间启动
time.sleep(30)
print("")
print("")

for instance_id in created_instance_ids:
    try:
        # 确认实例变为"运行中"状态
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
    except ServerException as e:
        print("设置自动释放时间失败，错误信息:", e.error_code, "-", e.message)
    except ClientException as e:
        print("设置自动释放时间失败，错误信息:", e.error_code, "-", e.message)

print("")
print("")
