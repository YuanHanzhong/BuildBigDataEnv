#!/usr/bin/env python
# coding=utf-8
import json
import time
from aliyunsdkecs.request.v20140526.AllocatePublicIpAddressRequest import AllocatePublicIpAddressRequest

import traceback
import os
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest

# 配置访问密钥和密钥ID
ACCESS_KEY_ID = os.environ.get('ACCESS_KEY_ID')
ACCESS_SECRET = os.environ.get('ACCESS_SECRET')


# 设置地区
region_id = "cn-zhangjiakou"

# 初始化客户端
client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, region_id)

# 配置实例参数
instance_type = "ecs.u1-c1m8.large" # 实例规格
security_group_id = "sg-8vbap91nk99v1ypw280a"
vswitch_id = "vsw-8vbi4ohmz5c1nsoasmnkl"
image_ids = [
    "m-8vben2f0ysfmxp8p86o6", "m-8vbgy1yye4xwlqrj1lm4",
    "m-8vbccvbehw3dwynsoos8"
]

# 镜像和实例名称对应关系
image_to_instance_name_map = {
    image_ids[0]: "hadoop102",
    image_ids[1]: "hadoop103",
    image_ids[2]: "hadoop104"
}

# 内网地址和实例对应关系
image_to_private_ip_map = {
     image_ids[0]:"172.29.16.12",
     image_ids[1]:"172.29.16.13",
     image_ids[2]:"172.29.16.14"
}

# 遍历镜像ID，创建实例
for image_id in image_ids:
    # 创建实例请求
    request = RunInstancesRequest()
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
    request.set_InternetMaxBandwidthOut(100)  # 带宽峰值为100Mbps

    # 登录凭证: 使用镜像预设密码
    request.set_PasswordInherit(True)

    # 发送创建实例请求
    try:
        response = client.do_action_with_exception(request)
        response_json = json.loads(response.decode("utf-8"))
        instance_id = response_json.get("InstanceId")
        # print("实例创建成功，实例ID:", instance_id)



        # 分配公网IP
        allocate_public_ip_request = AllocatePublicIpAddressRequest()
        allocate_public_ip_request.set_InstanceId(instance_id)
        allocate_public_ip_response = client.do_action_with_exception(allocate_public_ip_request)
        allocate_public_ip_response_json = json.loads(allocate_public_ip_response.decode("utf-8"))
        public_ip = allocate_public_ip_response_json.get("IpAddress")

        # ...

        # print("分配公网IP成功，IP地址:", public_ip)

        # 启动实例
        start_instance_request = StartInstanceRequest.StartInstanceRequest()
        start_instance_request.set_InstanceId(instance_id)
        start_instance_response = client.do_action_with_exception(
            start_instance_request)
        # print("实例启动成功，实例ID:", instance_id)

        # 输出公网IP和主机名
        print(public_ip, image_to_instance_name_map[image_id])

    except ServerException as e:
        print("实例创建失败，错误信息:", e.error_code, "-", e.message)
    except ClientException as e:
        print("实例创建失败，错误信息:", e.error_code, "-", e.message)
while True:
    pass
