import scrapy
from scrapy.crawler import CrawlerProcess


class IpSpider(scrapy.Spider):
    name = "ip_spider"
    start_urls = ["https://www.baidu.com/s?wd=ip"]

    def parse(self, response):
        ip_element = response.xpath(
            "//div[contains(@class, 'c-border')]/div[contains(@class, 'c-row')]/span"
        )
        if ip_element:
            local_ip = ip_element.get().strip()
            print(f"本地公网IP地址是: {local_ip}")
        else:
            print("无法获取本地公网IP地址")


if __name__ == "__main__":
    process = CrawlerProcess(settings={"LOG_LEVEL": "ERROR"})
    process.crawl(IpSpider)
    process.start()
