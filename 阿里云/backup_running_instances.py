import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ServerException, ClientException
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest, CreateImageRequest

# 配置访问密钥和密钥ID
ACCESS_KEY_ID = "LTAI5t77RHozE1RjuHt3Duxd"
ACCESS_SECRET = "m5lCvhHQTU9epnrRdDiUCcsDMSSZlg"

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
    # 需要重新设置名字
    request.set_ImageName(f"date_0422{instance_name}")
    request.set_ImageVersion("1.0")
    response = client.do_action_with_exception(request)
    response_json = json.loads(response.decode("utf-8"))
    return response_json["ImageId"]


if __name__ == "__main__":
    running_instances = get_running_instances()

    print("实例hadoop104, hadoop103, hadoop102的镜像ID分别为：")
    print("")
    for instance in running_instances:
        instance_id = instance["InstanceId"]
        instance_name = instance["InstanceName"]

        try:
            image_id = create_image(instance_id, instance_name)
            print(f"{image_id}")
        except ServerException as e:
            print(
                f"为实例 {instance_name} 创建镜像失败，错误信息: {e.error_code} - {e.message}"
            )
        except ClientException as e:
            print(
                f"为实例 {instance_name} 创建镜像失败，错误信息: {e.error_code} - {e.message}"
            )
