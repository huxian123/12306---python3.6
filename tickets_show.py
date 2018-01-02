# coding:utf-8
"""
usage:
按提示输入出发日期、始发站、终点站
"""
import requests
from docopt import docopt
from stations import stations
from prettytable import PrettyTable
from colorama import init, Fore
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import copy
import json
init()



def _get_keys(station_eg):
    for key in stations:
        if stations[key] == station_eg:
            return key


class TrainsCollection:
    header = '车次 车站 时间 历时 一等 二等 软卧 硬卧 硬座 无座'.split()

    def __init__(self, available_trains,options=None):
        """
        查询到的火车班次集合

        :param available_trains:一个列车，包含可获得的火车班次，每个火车班次是一个字典
        :param options:查询选项，如高铁、动车，etc...
        """
        self.available_trains = available_trains
        self.options = options

    def _get_duration(self, raw_train):
        duration = raw_train.get('lishi').replace(':', '小时') + '分'
        if duration.startswith('00'):
            return duration[4:]
        if duration.startswith('0'):
            return duration[1:]
        return duration

    def _cut_train(self):
        seperated_info = []
        for i in range(len(self.available_trains)):
            train = self.available_trains[i].split('|')
            #print(train)
            if train[0] == 'null':
                continue
            else:
                seperated_info.append(train)
        dict_header = ['train_number', 'from_station', 'to_station', 'from_time', 'to_time'
            , 'spend_time', 'first_class', 'second_class', 'soft_sleeper', 'hard_sleeper', 'hard_seat', 'no_seat']
        refer_to_num = [3, 4, 5, 8, 9, 10, 31, 30, 23, 28, 29, 26]
        train_list = []
        train_dict = { }
        for times in range(len(seperated_info)):
            for key in range(len(dict_header)):
                if seperated_info[times][refer_to_num[key]]:
                    train_dict[dict_header[key]] = seperated_info[times][refer_to_num[key]]
                else:
                    train_dict[dict_header[key]] = '--'
            train_list.append(copy.deepcopy(train_dict))
        return train_list

    def trains(self):
        for raw_train in self._cut_train():
            train_no = raw_train['train_number']
            initial = train_no[0].lower()

            #if not self.options or initial in self.options:
            train = [
                train_no,
                '\n'.join([Fore.GREEN + _get_keys(raw_train['from_station']) + Fore.RESET,
                           Fore.RED + _get_keys(raw_train['to_station']) + Fore.RESET]),
                '\n'.join([Fore.GREEN + raw_train['from_time'] + Fore.RESET,
                           Fore.RED + raw_train['to_time'] + Fore.RESET]),
                raw_train['spend_time'],
                raw_train['first_class'],
                raw_train['second_class'],
                raw_train['soft_sleeper'],
                raw_train['hard_sleeper'],
                raw_train['hard_seat'],
                raw_train['no_seat'],
                ]
            yield train

    def pretty_print(self):
        pt = PrettyTable()
        pt._set_field_names(self.header)
        for train in self.trains():
            pt.add_row(train)
        print(pt)

