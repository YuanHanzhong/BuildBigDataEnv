import re
import subprocess


def get_new_image_ids():
    result = subprocess.run(['python', '/Users/jack/code/python-scripts/backupHadoop.py'], text=True,
                            capture_output=True)
    output = result.stdout
    print("new ImageIds:")
    print(output)
    match = re.search(r'image_ids = \[\s*(.*?)\s*\]', output, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        raise ValueError("image_ids array not found in script output")


def update_script(new_image_ids):
    with open('/Users/jack/code/python-scripts/createBigData.py', 'r') as file:
        data = file.read()

    # 构建一个新的 image_ids 部分
    new_image_ids_section = f'image_ids = [\n    {new_image_ids},\n]'

    # 使用正则表达式替换旧的 image_ids 部分
    updated_data = re.sub(r'(image_ids = \[.*?\])', new_image_ids_section, data, flags=re.DOTALL)

    with open('/Users/jack/code/python-scripts/createBigData.py', 'w') as file:
        file.write(updated_data)

    print("script updated.")


if __name__ == "__main__":
    new_image_ids = get_new_image_ids()
    update_script(new_image_ids)
