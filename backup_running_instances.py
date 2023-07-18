import json
import os

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest, CreateImageRequest
from datetime import datetime

# 获取当前日期
current_date = datetime.now().strftime("%Y%m%d%H:%M")
# 配置访问密钥和密钥ID
ACCESS_KEY_ID = os.environ.get('ACCESS_KEY_ID')
ACCESS_SECRET = os.environ.get('ACCESS_SECRET')


# 设置地区
region_id = "cn-zhangjiakou"

# 初始化客户端
client = AcsClient(ACCESS_KEY_ID, ACCESS_SECRET, region_id)


def get_running_instances():
    request = DescribeInstancesRequest.DescribeInstancesRequest()
    request.set_Status("Running")
    response = client.do_action_with_exception(request)
    response_json = json.loads(response.decode("utf-8"))
    return response_json["Instances"]["Instance"]


def create_image(instance_id, instance_name):
    request = CreateImageRequest.CreateImageRequest()
    request.set_InstanceId(instance_id)
    # 设定镜像名字
    request.set_ImageName(f"{instance_name}_{current_date}")
    request.set_ImageVersion("1.0")
    response = client.do_action_with_exception(request)
    response_json = json.loads(response.decode("utf-8"))
    return response_json["ImageId"]


if __name__ == "__main__":
    running_instances = get_running_instances()

    print("镜像创建完成...")
    print()
    print("按住 option+shift 块选, 复制粘贴")
    for instance in running_instances:
        instance_id = instance["InstanceId"]
        instance_name = instance["InstanceName"]

        try:
            image_id = create_image(instance_id, instance_name)
            # image_ids = [
            #     "m-8vben2f0ysfmxp8p86o6",  # hadoop104
            #     "m-8vbgy1yye4xwlqrj1lm4",  # hadoop103
            #     "m-8vbccvbehw3dwynsoos8"  # hadoop102
            # ]
            # print(f"\"{image_id}\"  # {instance_name}")
            # print(f"{image_id}  # {instance_name}")
            print(f"{image_id}")



        except ServerException as e:
            print(
                f"为实例 {instance_name} 创建镜像失败，错误信息: {e.error_code} - {e.message}"
            )
        except ClientException as e:
            print(
                f"为实例 {instance_name} 创建镜像失败，错误信息: {e.error_code} - {e.message}"
            )
