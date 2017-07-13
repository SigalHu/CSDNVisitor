import re
from random import choice
import requests
import bs4
from print_manager import *

class ProxyIP:
	__url = 'http://www.xicidaili.com/nn'
	__headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;',
	             'Accept-Encoding': 'gzip',
	             'Accept-Language': 'zh-CN,zh;q=0.8',
	             'Referer': 'http://www.xicidaili.com/',
	             'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36'}
	__proxy_ip = None

	def __init__(self, num=100):
		self.__proxy_ip = self.__get_proxy_ip(num=num)

	def __get_proxy_ip(self, num=100):
		try:
			r = requests.get(self.__url, headers=self.__headers)
			soup = bs4.BeautifulSoup(r.text, 'html.parser')
			data = soup.table.find_all('td', limit=num * 10)
			ip_compile = re.compile(r'<td>(\d+\.\d+\.\d+\.\d+)</td>')
			port_compile = re.compile(r'<td>(\d+)</td>')
			ips = re.findall(ip_compile, str(data))
			ports = re.findall(port_compile, str(data))
			proxyIP = ['http://%s:%s' % (ip, port) for ip, port in zip(ips, ports)]
		except Exception as ex:
			show_error('获取代理ip失败！\n%s' % ex)
		else:
			return proxyIP

	def __is_valid(self, ip):
		try:
			requests.get('http://www.baidu.com/', timeout=5,proxies={'http': ip})
		except Exception as ex:
			return False
		else:
			return True

	def get_ip(self):
		if self.__proxy_ip is None or len(self.__proxy_ip) == 0:
			self.__proxy_ip = self.__get_proxy_ip()
			if self.__proxy_ip is None:
				return
		ip = choice(self.__proxy_ip)

		while not self.__is_valid(ip):
			self.__proxy_ip.remove(ip)
			if len(self.__proxy_ip) == 0:
				self.__proxy_ip = self.__get_proxy_ip()
				if self.__proxy_ip is None:
					return
			ip = choice(self.__proxy_ip)
		return ip

if __name__ == '__main__':
	ips = ProxyIP()
	print(ips.get_ip())
