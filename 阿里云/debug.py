# 导入必要的库
import json
import time
import traceback
import datetime

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from aliyunsdkecs.request.v20140526.RunInstancesRequest import RunInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526.DescribeInstanceAttributeRequest import DescribeInstanceAttributeRequest
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkecs.request.v20140526 import CreateInstanceRequest, AllocatePublicIpAddressRequest, StartInstanceRequest

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
    "m-8vben2f0ysfmjq3ti6xz": "172.29.16.13",
    "m-8vb7rdiuu3e6ctc2he6t": "172.29.16.14",
    "m-8vbhjx185w94owpeci1x": "172.29.16.15"
}

# 遍历镜像ID，创建实例
for image_id in image_ids:
    # 创建实例请求
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
        # print("实例创建成功，实例ID:", instance_id)

        # ...
        # 分配公网IP
        allocate_public_ip_request = AllocatePublicIpAddressRequest.AllocatePublicIpAddressRequest(
        )
        allocate_public_ip_request.set_InstanceId(instance_id)
        allocate_public_ip_response = client.do_action_with_exception(
            allocate_public_ip_request)
        allocate_public_ip_response_json = json.loads(
            allocate_public_ip_response.decode("utf-8"))
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
