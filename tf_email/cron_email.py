#!/usr/bin/env python
# coding:utf-8
#@author: xiongyan
import time, random, os
import MySQLdb as mysql
import sys
import urllib
import threading
from getopt import gnu_getopt, GetoptError
reload(sys)
sys.setdefaultencoding("utf-8")
#print sys.getdefaultencoding()

#默认执行小时
EXEC_HOURS = 24 
#检查邮件列表是否更新URL
URL_A = "http://nc.tengfang.net/cron.php/Email/prepare_news"
URL_B = "http://nc.tengfang.net/cron.php/Email/prepare_email_content"
CONTENT_FILE_NAME = "./data/mail_body.txt" #正文模板

#--链接数据库--
Host = "127.0.0.1"
Db = "test"
try:
    cursor = mysql.connect(user="root", passwd="", host=Host, db=Db, \
    charset='utf8').cursor()
except mysql.OperationalError as err:
    print(err)
    exit(1)
"""
finally:
    print(u"datebase connect fail.")
"""

help_info = u"cron_email.py [ -m | --menu | -h | --hours ] \n"
u"\t-m or --menu\t显示帮助菜单\n"
u"\t-h or --hours 指定多少小时执行一次(1-24)\n"

def help():
	print(help_info)

#检查更新

def check_url_update(php_url):
    try:
        src = urllib.urlopen(php_url)
        text = src.read()
        print(text)
        return str(text)
    except Exception, e:
        print(str(e))
        return False
    finally:
        src.close()

#生成邮件内容

def make_mail_body(msg, name, lpname):
    path = os.getcwd()
    file = os.path.join(path, CONTENT_FILE_NAME)
    content = open(file, 'rb')
    data = content.read()
    try:
        data = data.decode('utf-8')
    except:
        data = data.decode('utf-8', 'ignore')
    content.close()
    #替换内容
    rand_key = random.randint(10000000, 99999999)
    body = data.replace('###name###', name) #毛先生
    body = body.replace('###rand_no###', str(rand_key)) #腾房字
    body = body.replace('###lpname###', lpname) #代表楼盘
    body = body.replace('###content###', msg) #加入内容
    return body


class load_mail:
    #ip_file    = "ip.txt"    #换IP记录
    #mail_file  = "yinhu_mail.txt"#发件人列表存放文件
    MAIL_LIST = list()
    MAIL_SUM = 0

    #初始化
    def __init__(self):
        """self.mail_list   = mail_text.split("\n") #邮箱列表
        self.mail_count  = len(self.mail_list)     #总数"""
        self.MAIL_SUM = self.get_all() #统计

    #获取发件箱
    def get_all(self):
        sql="SELECT count(*) as sum FROM `t_queue_email` WHERE sent=0"
        rs = cursor.execute(sql)
        vo = cursor.fetchone()
        return vo[0]

    #获取收件箱
    def get_to_mail(self):
        data={}
        sql="SELECT %s FROM `t_queue_email` WHERE sent=0 ORDER BY id ASC " \
            "LIMIT 0, 1"%("id,content,receiver_email,username,lpname_etc")
        rs = cursor.execute(sql)
        vo = cursor.fetchone()
        if len(vo)>0:
            #print(vo)
            uname=str(vo[3])
            lpetc=str(vo[4])
            #生成内容
            data["body"]= make_mail_body(msg=str(vo[1]), name=uname, lpname=lpetc) 
            data["title"]= u"尊敬的%s,您在腾房网订阅的%s楼盘动态已有更新" \
            %(uname, lpetc)
            data["to_email"] = str(vo[2])
            data["uname"] = uname
            #print(data["uname"])
            #exit(1)
            self.update_status(id=str(vo[0]))
            return data
        else:
            return False

    #修改状态
    def update_status(self, id):
        curr_time = time.time()
        sql_update="UPDATE `t_queue_email` SET sent=1,sent_time=%s WHERE id=%s"
        param = (curr_time, id)
        #print(param)
        rs = cursor.execute(sql_update, param)
        return rs

#每24小时检查执行一次
def do_send_and_check():
    global EXEC_HOURS
    global t #Notice: use global variable!
    print("doing...")
    #检查PHP数据更新
    rs1 = check_url_update(php_url=URL_A)
    time.sleep(3)
    if rs1 == "1":
        rs2 = check_url_update(php_url=URL_B)
        time.sleep(3)
        if rs2 != "1":
            print("URL_B Update Error!")
    else:
        print("URL_A Update Error!")
    #发送邮件start
    import send
    x=load_mail()
    x.get_all() #统计
    for i in range(x.MAIL_SUM):
        #print(i)
        vo=x.get_to_mail() #生成发送内容
        if vo != False:
            fa = send.XMail()
            fa.sendwithoutattachment(vo) #无附件发信
            #print("famail 1")
            time.sleep(5) #隔5秒发信一封
    #发送邮件end
    cursor.close() #--关闭数据库连接--

    t = threading.Timer(3600.0*EXEC_HOURS, do_send_and_check)
    t.start()

#主函数
if __name__ == '__main__':
    # 解析命令行参数
    try:
        opts, args = gnu_getopt(sys.argv[1:], "mh:", ["menu", "hours="])
    except GetoptError, err:
        print str(err)
        help()
        exit(2)
    hours = ""
    for o, a in opts:
        if o in ("-m", "--menu"):
            help()
            exit(0)
        elif o in ("-h", "--hours"):
            hours = a
        else:
            print(u"未知选项")
            help()
            exit(2)
    if not hours:
        help()
        exit(2)
    
    EXEC_HOURS = int(hours)
    print("Tengfang Corn Email System is Runing...")
    #5s后新开线程执行do_send_and_check
    t = threading.Timer(5.0, do_send_and_check) 
    t.start()

    """x=load_mail()
    vo=x.get_to_mail() #生成发送内容
    #--关闭数据库连接--
    cursor.close()
    if vo != False:
        import send
        fa = send.XMail()
        fa.sendwithoutattachment(vo) #无附件发信
"""
