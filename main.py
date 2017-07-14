import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import datetime
import random
import time
import threading
import proxy_ip

_thread_blog_list = []
_thread_blog_probability = []


class Visitor(threading.Thread):
	def __init__(self, visitor_id, ips,thread_lock, visit_num=10, min_sleep_time=1, max_sleep_time=10):
		threading.Thread.__init__(self)
		self.__visitor_id = visitor_id
		self.__ips = ips
		self.__visit_num = visit_num
		self.__min_sleep_time = min_sleep_time
		self.__max_sleep_time = max_sleep_time
		self.__thread_lock = thread_lock

	def __get_blog_index(self, probability):
		global _thread_blog_probability
		if probability < 0 or probability > 1:
			raise Exception('概率应在0--1之间！')
		range_max = 0
		for ii in range(len(_thread_blog_probability)):
			range_max += _thread_blog_probability[ii]
			if probability < range_max:
				return ii
		return len(_thread_blog_probability) - 1

	def run(self):
		global _thread_blog_list
		if self.__max_sleep_time < self.__min_sleep_time:
			raise Exception('访问者 %d：等待时间范围设置错误！' % self.__visitor_id)

		print('访问者 %d：获取代理ip...' % self.__visitor_id)
		self.__thread_lock.acquire()
		proxy_handler = urllib.request.ProxyHandler({'http': self.__ips.get_ip()})
		self.__thread_lock.release()
		opener = urllib.request.build_opener(proxy_handler)
		urllib.request.install_opener(opener)

		for ii in range(self.__visit_num):
			idx = self.__get_blog_index(random.random())
			print('访问者 %d：已访问 %d/%d 次，此次访问《%s》！' % (
				self.__visitor_id, ii + 1, self.__visit_num, _thread_blog_list[idx]['标题']))
			try:
				urllib.request.urlopen(_thread_blog_list[idx]['链接'])
				time.sleep(random.uniform(self.__min_sleep_time, self.__max_sleep_time))
			except Exception as ex:
				print(ex)
				print('访问者 %d：重新获取代理ip...' % self.__visitor_id)
				self.__thread_lock.acquire()
				proxy_handler = urllib.request.ProxyHandler({'http': self.__ips.get_ip()})
				self.__thread_lock.release()
				opener = urllib.request.build_opener(proxy_handler)
				urllib.request.install_opener(opener)
		print('访问者 %d：访问完成！' % self.__visitor_id)


class CSDNVisitor:
	__blog_list = []
	__blog_probability = []

	@property
	def blog_list(self):
		return self.__blog_list

	@property
	def blog_probability(self):
		return self.__blog_probability

	def __init__(self, blog_list_url, date_weight=1, hits_weight=1):
		month_dict = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': '9', '十': 10, '十一': 11,
		              '十二': 12}
		url_info = urllib.parse.urlsplit(blog_list_url)

		self.__blog_list = []
		while True:
			resq = urllib.request.urlopen(blog_list_url)
			html_page = resq.read().decode('utf-8')
			soup = BeautifulSoup(html_page, 'html.parser')
			blog_detail = soup.find_all('dl', class_='list_c clearfix')
			for detail in blog_detail:
				bloginfo = {'标题': None,
				            '链接': None,
				            '日期': None,
				            '访问量': None}
				try:
					bloginfo['标题'] = detail.h3.get_text()
					bloginfo['链接'] = urllib.parse.urlunsplit(
						(url_info.scheme, url_info.netloc, detail.h3.a['href'], url_info.query, url_info.fragment))
					date_t = detail.find('div', class_='date_t')
					date_b = detail.find('div', class_='date_b')
					bloginfo['日期'] = datetime.date(int(date_t.span.string), month_dict[date_t.em.string],
					                               int(date_b.string))
					visit_num = detail.find('i', class_='fa fa-eye').next_sibling.get_text().strip('()')
					bloginfo['访问量'] = int(visit_num) if visit_num.isdigit() else 1

					self.__blog_list.append(bloginfo)
				except Exception as ex:
					print(ex)
			url_tag = soup.find('div', class_='pagelist').find('a', text='下一页')
			if url_tag is None:
				break
			blog_list_url = urllib.parse.urlunsplit(
				(url_info.scheme, url_info.netloc, url_tag['href'], url_info.query, url_info.fragment))
		self.__calculate_probability(date_weight, hits_weight)

	def __calculate_probability(self, date_weight=1, hits_weight=1):
		weight = date_weight + hits_weight
		date_weight /= weight
		hits_weight /= weight

		now_date = datetime.date.today() + datetime.timedelta(days=1)
		date_probability = []
		hits_probability = []
		date_total = 0
		hits_total = 0
		for blog in self.__blog_list:
			date_delta = (now_date - blog['日期']).days
			date_total += date_delta
			date_probability.append(date_delta)

			hits_total += blog['访问量']
			hits_probability.append(blog['访问量'])

		self.__blog_probability = []
		probability_total = 0
		for date, hits in zip(date_probability, hits_probability):
			probability = date_weight * date / date_total + hits_weight * hits / hits_total
			probability_total += probability
			self.__blog_probability.append(probability)
		self.__blog_probability = [ii / probability_total for ii in self.__blog_probability]

	def __get_blog_index(self, probability):
		if probability < 0 or probability > 1:
			raise Exception('概率应在0--1之间！')
		range_max = 0
		for ii in range(len(self.__blog_probability)):
			range_max += self.__blog_probability[ii]
			if probability < range_max:
				return ii
		return len(self.__blog_probability) - 1

	def start_visit(self, visit_num=10, min_sleep_time=1, max_sleep_time=10):
		if max_sleep_time < min_sleep_time:
			raise Exception('等待时间范围设置错误！')
		for ii in range(visit_num):
			idx = self.__get_blog_index(random.random())
			print('已访问 %d/%d 次，此次访问《%s》！' % (ii + 1, visit_num, self.__blog_list[idx]['标题']))
			try:
				urllib.request.urlopen(self.__blog_list[idx]['链接'])
				time.sleep(random.uniform(min_sleep_time, max_sleep_time))
			except Exception as ex:
				print(ex)
		print('访问完成！')

	def start_visit_plus(self, visitor_num=10, each_visit_num=10, min_sleep_time=1, max_sleep_time=10):
		global _thread_blog_list,_thread_blog_probability
		_thread_blog_list = self.__blog_list
		_thread_blog_probability = self.__blog_probability

		ips = proxy_ip.ProxyIP()
		thread_task = []
		thread_lock = threading.Lock()
		for ii in range(visitor_num):
			thread = Visitor(ii,ips,thread_lock,each_visit_num,min_sleep_time,max_sleep_time)
			thread.start()
			thread_task.append(thread)

		for thread in thread_task:
			thread.join()

def __main():
	url = r'http://blog.csdn.net/u000000000'
	csdn_visitor = CSDNVisitor(url)
	csdn_visitor.start_visit_plus()


if __name__ == '__main__':
	__main()
