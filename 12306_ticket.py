#-*- coding:utf-8 -*-
import requests
import urllib.parse
from stations import stations
from tickets import TrainsCollection
import ssl
import re
import time
from datetime import datetime,date
from collections import OrderedDict
import string
import random
import http.cookiejar as cookielib
from PIL import Image

ssl._create_default_https_context = ssl._create_unverified_context()


# 1  46,53
# 2  118,48
# 3  188,54
# 4  265,49
# 5  47,121
# 6  119,199
# 7  191,118
# 8  261,127

SEAT_TYPE = OrderedDict()
SEAT_TYPE['商务座'] = "9"
SEAT_TYPE['特等座'] = "P"
SEAT_TYPE['一等座'] = "M"
SEAT_TYPE['二等座'] = "O"
SEAT_TYPE['高级软卧'] = "5"
SEAT_TYPE['软卧'] = "4"
SEAT_TYPE['硬卧'] = "3"
SEAT_TYPE['软座'] = "2"
SEAT_TYPE['硬座'] = "1"
SEAT_TYPE['无座'] = "1"
SEAT_TYPE['其他'] = ""

class Poster(object):
    def __init__(self):
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:57.0) Gecko/20100101 Firefox/57.0'
        }

        cookie_jar = cookielib.LWPCookieJar()
        self._session = requests.session()
        self._session.headers = self._headers
        self._session.verify = False
        self._session.cookies = cookie_jar
        self._today = date.strftime(date.today(),"%Y-%m-%d")
        self._order_info = dict()
        self._train = dict()
        self._infos = dict()

    def check_date(self,date):
        date = time.strptime(date, "%Y-%m-%d")
        a = time.mktime(date)

        b = time.strptime(self._today,"%Y-%m-%d")
        c = time.mktime(b)



        if a < c:
            print('输入日期小于当前日期')
            return None
        else:
            return True




    def get_img(self):
        ret = self._session.get('https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&0.9735030659066763')
        codeImg = ret.content
        with open('./code.png','wb') as fn:
            fn.write(codeImg)
        return Image.open("./code.png")

    def captcha(self,number):
        switcher = {
            '1': '46,53',
            '2': '118,48',
            '3': '188,54',
            '4': '265,49',
            '5': '47,121',
            '6': '119,199',
            '7': '191,118',
            '8': '261,127'
        }
        p = []
        for i in str(number).split(','):
            p += (switcher.get(i).split(','))
        code = str(p).replace('[', '', 1).replace(']', '', 1).replace("'", "").replace(' ', '')
        print(code)
        return code


    def login(self):
        im = self.get_img()
        im.show()
        number = input('请输入验证码,多个以逗号隔开：')
        # p=[]
        # for i in str(number).split(','):
        #     p += (self.captcha(i).split(','))
        # code = str(p).replace('[','',1).replace(']','',1).replace("'","").replace(' ','')
        # print(code)
        data = {
            'answer': self.captcha(number),
            'login_site': 'E',
            'rand': 'sjrand'
        }
        ret = self._session.post('https://kyfw.12306.cn/passport/captcha/captcha-check',data=data).json()
        if ret['result_code'] == '4':
            print(ret['result_message'])
        else:
            print(ret['result_message'])
            self.login()
            return

        data = {
            'username': 'huxian12_',
            'password': 'yuji19890728',
            'appid': 'otn'
        }

        ret = self._session.post('https://kyfw.12306.cn/passport/web/login',data=data).json()
        if ret['result_code'] == 0:
            print(ret)
            data = {'appid':'otn'}
            ret = self._session.post('https://kyfw.12306.cn/passport/web/auth/uamtk',data=data).json()
            print(ret)
            newapptk = ret['newapptk']
            data = {'tk':newapptk}
            ret = self._session.post('https://kyfw.12306.cn/otn/uamauthclient',data=data).json()
            print(ret)
            return True
        else:
            print(ret['result_message'])
            return False

    def re_search(pattern, content):
        try:
            match = re.compile(pattern,re.S)
            #match = re.search(pattern1,content).group(1)
            return re.search(match, content).group(1)
        except AttributeError:
            return ""

    def check_login(self):
        if self.user_logined():
            #logger.info("-- account {0} login success [cookies]".format(username))
            print('登录信息有效')
            return True
        else:
            print('登录信息已超时，请重新登录')
            self._session.cookies.clear()
            self.login()


    def user_logined(self):
        data = {'_json_att': ''}
        ret = self._session.post('https://kyfw.12306.cn/otn/login/checkUser', data=data).json()
        #print(ret)
        return ret['data']['flag']


    def query_trains(self):
        train_date = input('请输入出发时间例如(2017-12-12):')
        from_station = input('请输入出发城市(长沙):')
        to_station = input('请输入到达城市(深圳):')
        print(stations.get(from_station), stations.get(to_station))
        if stations.get(from_station) is None or stations.get(to_station) is None or self.check_date(train_date) is None:
            print('出发时间、城市或者达到城市不合法，请重新输入')
            self.query_trains()
        else:
            print(train_date, from_station, to_station)
            ret = self._session.get('https://kyfw.12306.cn/otn/leftTicket/log?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.
                format(train_date, stations[from_station], stations[to_station])).json()
            print(ret)
            if ret['status'] == False:
                print(ret['messages'])
            else:
                self._infos['from_station'] = from_station
                self._infos['to_station'] = to_station
                self._infos['train_date'] = train_date
                return self._infos


    def query_tickets(self):
        ret = self._session.get('https://kyfw.12306.cn/otn/leftTicket/queryO?leftTicketDTO.train_date={}&leftTicketDTO.from_station={}&leftTicketDTO.to_station={}&purpose_codes=ADULT'.format(self._infos['train_date'], stations[self._infos['from_station']],stations[self._infos['to_station']])).json()
        print(ret)
        TrainsCollection(ret['data']['result']).pretty_print()
        ret_data = ret['data']
        if not ret_data:
            ret_data = None
            msg = "".join(ret['messages'])
            if not msg.strip():
                msg = "没有查询到结果, 请注意购票日期"
        else:
            b = input('请选择要预定的车次:')
            for p in ret_data['result']:
                a = p.split('|')
                if b == a[3]:
                    self._train['secertStr'] = a[0]
                    self._train['stationTrainCode'] = a[3]
                    self._train['train_no'] = a[2]
                    self._train['from_station'] = self._infos['from_station']
                    self._train['to_station'] = self._infos['to_station']
                    self._train['leftTicketStr'] = a[12]
                    self._train['train_date'] = self._infos['train_date']
                    self._train['train_location'] = a[15]
                    return self._train


    def submit_order_request(self):
        self.check_login()
        data = {
            'secretStr': urllib.parse.unquote(self._train['secertStr']),
            'train_date': self._train['train_date'],
            'back_train_date': self._train['train_date'],
            'tour_flag': 'dc',
            'purpose_codes': 'ADULT',
            'query_from_station_name': self._train['from_station'],
            'query_to_station_name': self._train['to_station'],
            'undefined': ''
        }
        ret = self._session.post('https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest', data=data).json()
        status = ret['status']
        if not status:
            print(ret['messages'])
        return status

    def confirm_passenger(self):
        data = {'_json_att': ''}
        ret = self._session.post('https://kyfw.12306.cn/otn/confirmPassenger/initDc', data=data).text
        submit_token = re.compile("var globalRepeatSubmitToken = '([a-z0-9]+)';", re.S)
        key_check_isChange = re.compile("'key_check_isChange':'([A-Z0-9]+)',", re.S)
        self._infos['REPEAT_SUBMIT_TOKEN'] = re.search(submit_token,ret).group(1)
        self._infos['key_check_isChange'] = re.search(key_check_isChange,ret).group(1)
        #print(self._infos)
        return self._infos

    def parse_train_date(self,date):
        week_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        month_name = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
        y, m, d = map(int, date.split("-"))
        weekday = datetime(y, m, d).weekday()
        # fix c locale
        return "{0} {1} {2} {3} 00:00:00 GMT+0800 (CST)".format(week_name[weekday], month_name[m-1], d, y)


    def request_passenger(self):
        self.confirm_passenger()
        data = {
        '_json_att': '',
        'REPEAT_SUBMIT_TOKEN': self._infos['REPEAT_SUBMIT_TOKEN']
        }
        ret = self._session.post('https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs',data=data).json()
        passengers = []
        status = ret['status']
        if status:
            for p in ret['data']['normal_passengers']:
                print(p['index_id'] + ':' + p['passenger_name'])
                passengers.append(p)
            return passengers

    def check_order_info(self):
        p = self.request_passenger()
        print(SEAT_TYPE)
        seat_type = input('请输入购买的车票类型：')
        index = input('请输入购票人：')
        for i in range(len(p)):
            if index == p[i]['index_id']:
                data = {
                    'cancel_flag': '2',
                    'bed_level_order_num': '000000000000000000000000000000',
                    'passengerTicketStr': "{0},0,1,{1},{2},{3},{4},N".format(seat_type, p[i]['passenger_name'],p[i]['passenger_id_type_code'],p[i]['passenger_id_no'],p[i]['mobile_no']),
                    'oldPassengerStr': "{0},{1},{2},1_".format(p[i]['passenger_name'], p[i]['passenger_id_type_code'], p[i]['passenger_id_no']),
                    'tour_flag': 'dc',
                    'randCode': '',
                    'whatsSelect': '1',
                    '_json_att': '',
                    'REPEAT_SUBMIT_TOKEN': self._infos['REPEAT_SUBMIT_TOKEN']
                }
                ret = self._session.post('https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo', data=data).json()
                print(ret)
                self._infos['rand_code'] = ''
                submit_status = ret['data']['submitStatus']
                ifShowPassCode = ret['data']['ifShowPassCode']
                if ifShowPassCode == 'Y':
                    self.checkRandCodeAnsyn()
                if not submit_status:
                    err_msg = ret['data']['errMsg']
                    if not err_msg:
                        err_msg = "检测订单信息: " + ret['messages']
                self._train['seat_type'] = seat_type
                self._train['passengerTicketStr'] = "{0},0,1,{1},{2},{3},{4},N".format(seat_type, p[i]['passenger_name'],p[i]['passenger_id_type_code'],p[i]['passenger_id_no'], p[i]['mobile_no'])
                self._train['oldPassengerStr'] = "{0},{1},{2},1_".format(p[i]['passenger_name'], p[i]['passenger_id_type_code'],p[i]['passenger_id_no'])
                return submit_status



    def get_quque_count(self):
        print(self._train['train_date'])
        data = {
            'train_date': self.parse_train_date(self._train['train_date']),
            'train_no': self._train['train_no'],
            'stationTrainCode': self._train['stationTrainCode'],
            'seatType': self._train['seat_type'],
            'fromStationTelecode': stations[self._train['from_station']],
            'toStationTelecode': stations[self._train['to_station']],
            'leftTicketStr': self._train['leftTicketStr'],
            'purpose_codes': '00',
            'train_location': self._train['train_location'],
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self._infos['REPEAT_SUBMIT_TOKEN']
        }
        ret = self._session.post('https://kyfw.12306.cn/otn/confirmPassenger/getQueueCount',data=data).json()
        status = ret['status']
        if not status:
            print(ret['messages'])
            return False
        ticket = ret['data']['ticket']
        if not ticket:
            print("前面已有{0}人在排队".format(ret['data']['count']))
        return bool(ticket)

    def getpasscodenew(self):
        ret = self._session.get('https://kyfw.12306.cn/otn/passcodeNew/getPassCodeNew?module=passenger&rand=randp&{}'.format(random.random))
        codeImg = ret.content
        with open('./second_code.png', 'wb') as fn:
            fn.write(codeImg)
        return Image.open("./second_code.png")


    def checkRandCodeAnsyn(self):
        im = self.getpasscodenew()
        im.show()
        number = input('请输入验证码,多个以逗号隔开：')
        self._infos['rand_code'] = self.captcha(number)
        data = {
            'randCode': self._infos['rand_code'],
            'rand': 'randp',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self._infos['REPEAT_SUBMIT_TOKEN']
        }
        ret = self._session.post('https://kyfw.12306.cn/otn/passcodeNew/checkRandCodeAnsyn',data=data).json()
        print(ret)
        status = ret['data']['result']
        if status == '0':
            print('验证码错误，请重新输入'+ ret['data']['msg'])
            self.checkRandCodeAnsyn()
        else:
            print('验证码正确')
            return ret['data']['msg']



    def confirm_order(self):
        data = {
            'passengerTicketStr': self._train['passengerTicketStr'],
            'oldPassengerStr': self._train['oldPassengerStr'],
            'randCode': self._infos['rand_code'],
            'purpose_codes': '00',
            'key_check_isChange': self._infos['key_check_isChange'],
            'leftTicketStr': self._train['leftTicketStr'],
            'train_location': self._train['train_location'],
            'choose_seats': '',
            'seatDetailType': '000',
            'whatsSelect': '1',
            'roomType': '00',
            'dwAll': 'N',
            '_json_att': '',
            'REPEAT_SUBMIT_TOKEN': self._infos['REPEAT_SUBMIT_TOKEN']
        }
        print(data)
        ret = self._session.post('https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue',data=data).json()
        print(ret)
        submit_status = ret['data']['submitStatus']
        if not submit_status:
            print("确认订单失败: " + str(ret['data']['errMsg']))
            self.confirm_order()
        return submit_status


    def query_order(self):
        rand = ''.join(str(time.time()).split('.'))
        ret = self._session.get('https://kyfw.12306.cn/otn/confirmPassenger/queryOrderWaitTime?random={}&tourFlag=dc&_json_att=&REPEAT_SUBMIT_TOKEN={}'.format(rand[0:13],self._infos['REPEAT_SUBMIT_TOKEN'])).json()
        print(ret)
        data = ret['data']
        if data['orderId'] is None:
            self.query_order()
        else:
            orderId = data['orderId']
            data = {
                'orderSequence_no': orderId,
                '_json_att': '',
                'REPEAT_SUBMIT_TOKEN': self._infos['REPEAT_SUBMIT_TOKEN']
            }
            ret = self._session.post('https://kyfw.12306.cn/otn/confirmPassenger/resultOrderForDcQueue', data=data).json()
            print(ret)
            status = ret['status']
            submitStatus = ret['data']['submitStatus']
            if not status:
                print(ret['messages'])
                return False
            else:
                if not submitStatus:
                    print(ret['data']['errMsg'])
                    return False
                else:
                    return True

    def query_order_nocomplete(self):
        self.check_login()
        data = {
            '_json_att':''
        }
        ret = self._session.post('https://kyfw.12306.cn/otn/queryOrder/queryMyOrderNoComplete',data=data).json()
        print(len(ret))
        if len(ret) >= 6 :
            result = ret['data']
            #print(result)
            if 'orderDBList' in result.keys():
                orderinfo = result['orderDBList']
                print(orderinfo[0]['sequence_no'])
                print(orderinfo[0]['tickets'][0]['stationTrainDTO'])
                print(orderinfo[0]['tickets'][0]['passengerDTO'])
            else:
                ordercacheDTO = result['orderCacheDTO']
                print(ordercacheDTO['message']['message'] + ':' + str(ordercacheDTO['array_passser_name_page']))
            return False
        else:
            print('无待支付订单')
            return True


    def grab_tickets(self):
        ret = self.query_order_nocomplete()

        ret = self.query_trains()
        print(ret)
        if not ret:
            print('输入是否有误,请重新检查')
        ret = self.query_tickets()
        if not ret:
            print('查询错误，请重试')
            return False


        if not ret:
            return False

        time.sleep(3)
        ret = self.submit_order_request()
        print(ret)
        if not ret:
            return False

        ret = self.check_order_info()
        print(ret)
        if not ret:
            return

        ret = self.get_quque_count()
        print(ret)
        if not ret:
            return

        time.sleep(3)

        ret = self.confirm_order()
        if not ret:
            return

        ret = self.query_order()


poster = Poster()
poster.grab_tickets()




