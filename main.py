# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import urllib.request
from bs4 import BeautifulSoup

from time import sleep
import datetime
#from datetime import datetime
#import Adafruit_DHT as DHT
import Adafruit_DHT
#import adafruit_dht
import slackweb
import csv

from decimal import ROUND_HALF_UP, Decimal

#import traceback

PIN = 23

#csv_file
csv_file_name = '/home/zen/Documents/Geek/TemperatureHumidity/temp_humi.csv'
api_csv_file_name = '/home/zen/Documents/Geek/TemperatureHumidity/temp_humi_api.csv'

#slack proj-temperature_humidity
slack = slackweb.Slack(url='https://hooks.slack.com/services/#####/####/#####')

start_times=0 #from 0 min
get_times=20 #every 20 min
count=0
#dht_device = adafruit_dht.DHT11(PIN)
dht_sensor = Adafruit_DHT.DHT22
#humidity, temperature = Adafruit_DHT.read_retry(dht_sensor, PIN)

def str2float(weather_data):
    try:
        return float(weather_data)
    except:
        return 0

def scraping(url, date):

    # 気象データのページを取得
    html = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(html, 'html.parser')
    trs = soup.find('table', { 'class' : 'data2_s' })

    data_list = []
    data_list_per_hour = []

    # table の中身を取得
    for tr in trs.findAll('tr')[2:]:
        tds = tr.findAll('td')

        if tds[1].string == None:
            break

        data_list.append(format(date, '%Y/%m/%d'))
        data_list.append(tds[0].string+'時') # 時
        data_list.append(str2float(tds[4].string)) # 気温(℃)
        data_list.append(str2float(tds[7].string)) # 湿度(%)

        data_list_per_hour.append(data_list)

        data_list = []

    return data_list_per_hour

def create_csv(file_name, datas):
    with open(file_name, 'a') as input_f:
        writer = csv.writer(input_f, lineterminator='\n')
        writer.writerow(datas)

        df = pd.read_csv(file_name)
        tail_data = df.tail(1)
        pre_data = np.array(tail_data)
        # 例）pre_data = [['2022/09/05' '16時20分33秒' 27 70]]
        # 例）datas = ['2022/09/05', '16時22分44秒', 27, 70]

        str = datas[0] + ' ' + datas[1]
        #print('str: ', str)

        tdatetime = datetime.datetime.strptime(str, '%Y/%m/%d %H時%M分%S秒')
        #time = datetime.datetime(time)
        #print('tdatetime: ', tdatetime)

        # 毎日1時頃に更新されるデータなので、7時に取得
        if((tdatetime.hour == 7) and (start_times <= tdatetime.minute < start_times+get_times)): # 毎日1時頃に更新されるデータなので、２時に取得
            # データ取得開始・終了日 例）datas[0] = 2022/08/31
            year = tdatetime.year
            month = tdatetime.month
            day = tdatetime.day
            start_date = datetime.date(year, month, day)

            # CSV の列
            fields = ['日付', '時間', '気温', '湿度']

            #with open(file_name, 'w') as f:
            with open(api_csv_file_name, 'a') as output_f:
                writer = csv.writer(output_f, lineterminator='\n')
                writer.writerow(fields)

                date = start_date - datetime.timedelta(days=1)
                print('date', date)
                #while date != end_date + datetime.timedelta(1):

                # 対象url（会津）
                url = 'http://www.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?' \
                        'prec_no=36&block_no=47570&year=%d&month=%d&day=%d&view='%(date.year, date.month, date.day)
                        #https://www.data.jma.go.jp/obd/stats/etrn/view/10min_s1.php?prec_no=36&block_no=47570&year=2022&month=8&day=29&view=p1
                        #https://www.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php?prec_no=36&block_no=47570&year=2022&month=8&day=29&view=p1

                data_per_day = scraping(url, date)

                for dpd in data_per_day:
                    writer.writerow(dpd)

                #date += datetime.timedelta(1)

        # for data in datas:
        #     writer.writerow(data)



while True:
    try:
        #for i in range(5): #代わりにRaspberry Piを再起動させて、その時に実行
        while True:
            #temp = dht_device.temperature
            #temp = temperature
            #humi = dht_device.humidity
            #humi = humidity
            #result = instance.read()
            #temp = result.temperature
            #humi = result.humidity
            humi, temp = Adafruit_DHT.read_retry(dht_sensor, PIN)
            a_temp = Decimal(str(temp))
            a_humi = Decimal(str(humi))

            str_temp = a_temp.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
            str_humi = a_humi.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)

            temp = float(str_temp)
            humi = float(str_humi)
            #異常な値なら再取得
            if ((humi > 90) or (temp > 50)):
                print('- error:', temp, humi)
                sleep(0.1)
                continue
            break

        date = datetime.datetime.now().strftime('%Y/%m/%d')
        time = datetime.datetime.now().strftime('%H時%M分%S秒')

        print("+", date, time)
        print("| 温度=",temp,"度")
        print("| 湿度=",humi, "%")

        #CSV Fileに書き込み
        ldate = [date, time]
        ldata = [temp, humi]
        #datas = [date, time, temp, humi]
        # with open(csv_file_name, 'a') as exf:
        #     writer = csv.writer(exf, lineterminator='\n')
        #     writer.writerow(ldate+ldata)
        datas = ldate + ldata
        #print('datas: ', datas)
        create_csv(csv_file_name, datas)

        #Slackに通知
        data = date+' '+time+'\r\n 気温：' + str(temp) + '℃　湿度：' +str(humi) + '％ \r\n'
        temp_data = data
        slack.notify(text=temp_data)

        #20分ごとにデータを取得
        #sleep(1200)

    except Exception as e:
        if(count<4):
            error = str('Error: ')+str(e)
            slack.notify(text=error)
            print(error)
            #print(traceback.format_exc())
            count=count+1
            continue
        break

    # finally:
    #     #GPIO.cleanup()

    break
