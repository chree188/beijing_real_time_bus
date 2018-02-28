北京实时工具 API 接口解析 demo
==============================

Usage
--------
real_time_bus_only_text.py 和 real_time_bus_with_coording.py 使用方法一样

默认 300内:
python real_time_bus_only_text.py

6 路:
python real_time_bus_only_text.py 6

6 路另一个方向:
python real_time_bus_only_text.py 6 -r


说明
-----------

北京实时公交的基础数据应该还是掌握在官方手里，
我所知道的面向大众的就两个地方可以获取：

1）web端的 http://www.bjbus.com/

2）移动端的 http://www.bjjtw.gov.cn/ztlm/bjssgj/


通过对比发现，
两处获取的数据还不一样。
而且 web 端的数据没有坐标，
但是路线比较全。

移动端的数据有路线的坐标、站点坐标、公交车坐标，
但是数据被加密了[捂脸笑]。


web 端接口使用思路
------------------

抓取接口比较简单，
要吐槽的是他们竟然把一个 HTML 的页面当做 JSON 的一个字段返回，
好吧，你们玩的开心就好，
反正 web 端的流量没人在意。

解析的话，用上 BeautifulSoup 库就可以解析了。


移动端使用思路
--------------

移动端的接口抓取的话，
我用的小提琴 + 我的安卓机，
苹果端的机器没有搞。

请求回来的数据需要解密，
刚开始比较头疼，
幸亏前面有人搞过（好几年前的工程了，不过思路很好）
https://github.com/wong2/beijing_bus
能把获取到的数据给解码了(RC4算法)。
但是问题是现在他们在请求的时候增加了 ABTOKEN 字段，
要不然请求后反馈说客户端没有授权。


没辙了，
只能按照前人的思路做逆向了，
用上
https://github.com/pxb1988/dex2jar 和
JD-GUI http://jd.benow.ca/ 
打开 JAR 包以后，
尼玛整个世界豁然开朗了，
果然连代码混淆都没有，
按照文件名都能猜到关键代码在 setHeader 函数里了。

TOKEN 的生成比较有意思，
用上了时间戳，
还有几个信息是写死的，
还有最后字符串是根据 URL 的地址有关系 (代码里叫 getPath)。
生成的时候一遍用 SHA1 算法，
然后用 MD5。
不过转到 Python 算法的话，
一两行代码就搞定了。

后来发现这个哥们已经做这套接口研究透了（还做了小程序）：
https://github.com/xuebing1110/rtbus
后悔没有早点发现。


一共三个主要的请求，

1）获取所有的路线名称和 Id 等基本信息

2）根据路线 Id 获取路线坐标和站点信息

3）获取公交车的位置
	记住这个请求里的 getPath 返回的是空空空空。


总结
------

春节期间干这事，
也是没谁了。

原来想要练习下 Python 的水平的，
现在看我的 Python 写的还是渣，
一点设计都没有，
都是面向过程的编程，
只能把这个项目作为 API 的使用 Demo了[捂脸]。

而且我的 markdown 写的也够渣的，
大家凑合看吧，
主要是看思路。


感谢及参考网址
--------------

https://github.com/xuebing1110/rtbus

https://github.com/wong2/beijing_bus

https://github.com/pxb1988/dex2jar

http://jd.benow.ca/

Python 官方文档等
