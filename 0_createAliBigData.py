import subprocess
import re

# 模拟 vim 按键, 解决 hosts 不更新问题
import subprocess


def get_host_entries():
    result = subprocess.run(['python', '/Users/jack/code/python-scripts/createBigData.py'], text=True,
                            capture_output=True)
    output = result.stdout
    print("将要替换的内容是: ")
    print(output)
    # 使用正则表达式提取 IP 地址和主机名
    host_entries = re.findall(r'(\d+\.\d+\.\d+\.\d+)\s+(\S+)', output)
    return host_entries


def update_hosts_file(host_entries):
    with open('/etc/hosts', 'r') as file:
        data = file.read()

    for ip, hostname in host_entries:
        # 构建正则表达式以查找和替换主机条目
        pattern = re.compile(rf'(\d+\.\d+\.\d+\.\d+)\s+{re.escape(hostname)}')
        data = pattern.sub(f'{ip} {hostname}', data)

    with open('/etc/hosts', 'w') as file:
        file.write(data)

    print("Hosts file updated.")


def vim_save_and_quit(file_path):
    # 使用 echo 命令发送 :wq 到 vim
    cmd = 'echo ":wq" | vim -E -s {}'.format(file_path)
    subprocess.run(cmd, shell=True, check=True)


if __name__ == "__main__":
    host_entries = get_host_entries()
    update_hosts_file(host_entries)
    # 为了解决 hosts 不更新问题. 需要手动模拟 vim 'esc'-->w-->q
    vim_save_and_quit("/etc/hosts")
