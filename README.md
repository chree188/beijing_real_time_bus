北京实时工具 API 接口解析 demo
==============================

Usage
--------
web_bus.py 和 mobile_bus.py 使用方法一样

默认 1路:
python web_bus.py

6 路:
python web_bus.py 6

6 路另一个方向:
python web_bus.py 6 -r


说明
-----------

北京实时公交的基础数据应该还是掌握在官方手里，
我所知道的面向大众的就两个地方可以获取：

1）北京公交集团: [web端](http://www.bjbus.com/)

2）北京公交集团: 移动端 [公交e路通](http://android.myapp.com/myapp/detail.htm?apkName=com.tianlutech.ebus&ADTAG=mobile)

3）北京交通委：移动端 [北京实时公交](http://www.bjjtw.gov.cn/ztlm/bjssgj/)


通过对比发现，
“公交集团” 和 “交通委” 的数据还不一样。
而且 “公交集团” 的路线比较全，
“web版” 数据没有坐标，
“公交e路通” 有坐标。
北京交通委的移动端的路线不太全，
但是有坐标信息。

根据前人的经验解析 “北京实时公交” 的数据比较容易，
“公交e路通” 的数据还没有解析成功，
也没找到可以参考的代码。


北京公交集团: web端解析思路
-----------------------------

抓取接口比较简单，
要吐槽的是他们竟然把一个 HTML 的页面当做 JSON 的一个字段返回，
这样是不是太浪费流量了。

解析的话，用上 BeautifulSoup 库就可以解析了。
重点是 “到站” 和 “途中” 是两个不同的状态，
我是对比和同一路线的不同结果才发现的。具体请看代码。


“北京实时公交” 解析思路
--------------------------

移动端的接口抓取的话，
我用的小提琴 + 安卓机，
苹果端的抓包没有搞。

请求回来的数据需要解密，
按照前人的思路做逆向，
用上
[dex2jar](https://github.com/pxb1988/dex2jar)
  和
[JD-GUI](http://jd.benow.ca/) 
打开 JAR 包以后就可以看源码了。
[参考网址](https://github.com/wong2/beijing_bus)。


后来发现有个哥们已经把 [这套接口研究透了](https://github.com/xuebing1110/rtbus)（还做了小程序)，
后悔没有早点发现。


一共三个主要的请求，

1）获取所有的路线名称和 Id 等基本信息

2）根据路线 Id 获取路线坐标和站点信息

3）获取公交车的位置


“公交e路通” 解析思路
--------------------------

这个程序做的还算不错的了，
而且用的是 NDK 开发的，
所以不好做逆向。

抓包还是上面一样，
但是还是没有找到 TOKEN 的生成规律。
这个 APP 的数据特别全（和北京公交集团的 web 端数据一致），
所以还是很有诱惑的。
留着以后再解析吧。


总结
------

原来想要练习下 Python 的水平的，
现在看我的 Python 写的还是渣，
一点设计都没有，
都是面向过程的编程，
只能把这个项目作为 API 的使用 Demo了[捂脸]。

而且我的 markdown 写的也够渣的，
大家凑合看吧。

已经做成了公众号【北京实时公交助手】，
欢迎关注。


感谢及参考网址
--------------

https://github.com/xuebing1110/rtbus

https://github.com/wong2/beijing_bus

https://github.com/pxb1988/dex2jar

http://jd.benow.ca/

Python 官方文档等
