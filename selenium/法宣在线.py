# -*- coding: utf-8 -*-

from selenium import webdriver
import time

# 打开谷歌浏览器，填写谷歌浏览器驱动的位置，python里 \ 代表转移，r 代表不转义，原始字符串
# WebDriver 实例对象，指明使用  chrome 浏览器驱动

web = webdriver.Chrome(r'd:\chromedriver.exe')

# 制定最大等待时间为10秒，后续所有的
# find_element或者find_elements之类的方法调用
# 都会采用这个策略：如果找不到元素，每隔半秒钟再去界面上查找，直到找到
# 或者过了最长时长。
web.implicitly_wait(20)

# 打开网站，输入网址
web.get('http://www.faxuanyun.com/')

user = web.find_element('css selector', '#userAccount').send_keys('17780838860')
print(user)
