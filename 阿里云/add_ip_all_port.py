import json
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import AuthorizeSecurityGroupRequest

access_key_id = "LTAI5t77RHozE1RjuHt3Duxd"
access_key_secret = "m5lCvhHQTU9epnrRdDiUCcsDMSSZlg"
region_id = "cn-zhangjiakou"

client = AcsClient(access_key_id, access_key_secret, region_id)


def add_ip_to_security_group(ip, security_group_id):
    request = AuthorizeSecurityGroupRequest.AuthorizeSecurityGroupRequest()
    request.set_SecurityGroupId(security_group_id)
    request.set_IpProtocol("all")
    request.set_PortRange("-1/-1")
    request.set_SourceCidrIp(ip)

    try:
        response = client.do_action_with_exception(request)
        response_data = json.loads(response)
        return response_data, True
    except ClientException as e:
        print(f"ClientException: {e}")
        return None, False
    except ServerException as e:
        print(f"ServerException: {e}")
        return None, False


if __name__ == "__main__":
    # 修改ip <==================================================================================
    ip = "120.245.114.128"
    security_group_id = "sg-8vbap91nk99v1ypw280a"
    result, success = add_ip_to_security_group(ip, security_group_id)

    if success:
        print("IP地址添加成功")
    else:
        print("IP地址添加失败")
