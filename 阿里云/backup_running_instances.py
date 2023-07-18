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

    # List to hold tuples of instance name and image ID
    images = []

    for instance in running_instances:
        instance_id = instance["InstanceId"]
        instance_name = instance["InstanceName"]

        # Only backup instances where the hostname starts with 'hadoop'
        if instance_name.startswith('hadoop'):
            try:
                image_id = create_image(instance_id, instance_name)
                # Add the instance name and image ID as a tuple to the list
                images.append((instance_name, image_id))

            except ServerException as e:
                print(
                    f"为实例 {instance_name} 创建镜像失败，错误信息: {e.error_code} - {e.message}"
                )
            except ClientException as e:
                print(
                    f"为实例 {instance_name} 创建镜像失败，错误信息: {e.error_code} - {e.message}"
                )

    # Sort the list of tuples based on the instance name (first item in each tuple)
    images.sort()
    print()
    print()


    print("image_ids = [")
    for i, image in enumerate(images):
        if i != len(images) - 1:
            print(f"    \"{image[1]}\",  # {image[0]}")
        else:
            print(f"    \"{image[1]}\"  # {image[0]}")
    print("]")


