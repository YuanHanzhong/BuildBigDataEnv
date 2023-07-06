from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_local_ip():
    try:
        # 创建webdriver实例
        driver = webdriver.Chrome()

        # 访问百度搜索
        driver.get("https://www.baidu.com/s?wd=ip")

        # 等待页面加载完成
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="2"]/div/div[1]/div[2]/div[1]/span')))

        # 获取IP地址元素

        ip_element = driver.find_element(
            By.XPATH, '//*[@id="2"]/div/div[1]/div[2]/div[1]/span')

        # 提取IP地址
        ip_address = ip_element.text

        # 关闭webdriver
        driver.quit()

        return ip_address
    except Exception as e:
        print(f"获取本地IP地址失败: {e}")
        return None


if __name__ == "__main__":
    local_ip = get_local_ip()
    if local_ip:
        print(f"本地公网IP地址是: {local_ip}")
    else:
        print("无法获取本地公网IP地址")
