from __future__ import unicode_literals
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage, 
    TextSendMessage,
    TemplateSendMessage,
    MessageTemplateAction,
    ImageSendMessage,
    ButtonsTemplate)
#import re
import configparser

#裁切IMG
from PIL import Image

#利用yf抓股價 matplotlib繪製圖表
import yfinance as yf
import mplfinance as mpf

#網站截圖
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

#上傳圖檔
import pyimgur

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('/opt/linebot/config.ini')
line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))

@app.route('/')
def index():
    return 'Hello World fuck'

# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        print(body, signature)
        handler.handle(body, signature)
        
    except InvalidSignatureError:
        abort(400)

    return 'OK'

#選單
@handler.add(MessageEvent, message=TextMessage)
def main(event):
    message = event.message.text
    if "股票 " in message:
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
            alt_text = "股票資訊",
            template = ButtonsTemplate(
                        #thumbnail_image_url ="", 可放圖片
                        title = message + "股票資訊",
                        text = "請點選想查詢的股票資訊",
                        actions = [
                            MessageTemplateAction(
                                label= message[3:] + " 個股基本資訊",
                                text= "個股基本資訊 " + message[3:]),
                            MessageTemplateAction(
                                label= message[3:] + " 歷史股利",
                                text= "歷史股利 " + message[3:]),
                            MessageTemplateAction(
                                label= message[3:] + " 歷史股價",
                                text= "歷史股價 " + message[3:])
                        ],   
                    )
            )
        )

    if "歷史股利 " in message:
        #截圖
        screenshot_dividend(message[5:])

        #上傳至圖庫再抓下來
        #傳送圖檔
        
        x = imr(message[5:])
        image_message = ImageSendMessage(
        original_content_url=x,
        preview_image_url=x
        )
            
        line_bot_api.reply_message(event.reply_token, image_message)

        #刪除圖片
        delete_pic(message[5:])

    if "個股基本資訊 " in message:
        #截圖
        screenshot_profile(message[7:])

        #上傳至圖庫再抓下來
        #傳送圖檔
        
        x = imr(message[7:])
        image_message = ImageSendMessage(
        original_content_url=x,
        preview_image_url=x
        )
            
        line_bot_api.reply_message(event.reply_token, image_message)

        #刪除圖片
        delete_pic(message[7:])
    
    if "歷史股價 " in message:
       
        plot_stcok_chart(message[5:])

        #上傳至圖庫再抓下來
        #傳送圖檔
        
        x = imr(message[5:])

        image_message = ImageSendMessage(
        original_content_url=x,
        preview_image_url=x
        )
            
        line_bot_api.reply_message(event.reply_token, image_message)

        #刪除圖片
        delete_pic(message[5:])

    if "K線圖 " in message:
        kline_words = message[4:]
        kline_words = kline_words.split("&")

        plot_stcok_k_chart(kline_words[0],kline_words[1])

        #上傳至圖庫再抓下來
        #傳送圖檔
        x = imr(kline_words[0])

        image_message = ImageSendMessage(
        original_content_url=x,
        preview_image_url=x
        )
            
        line_bot_api.reply_message(event.reply_token, image_message)

        #刪除圖片
        delete_pic(kline_words[0])

    if "指令" in message:
        message = TextSendMessage(text='功能一:股票 + 空格 + 想查詢的股票代碼\n' + '範例: 股票 0050\n' +
          '功能二:K線圖 + 空格 + 想查詢的股票代碼 + & + 開始日期\n' + '範例: K線圖 0050&2022-01-01')
        line_bot_api.reply_message(event.reply_token,message )

#截圖股利
def screenshot_dividend(stock):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.set_window_size(515,900)
    stock = str(stock)
    Url = "https://tw.stock.yahoo.com/quote/" + stock + "/dividend"
    driver.get(Url)

    #滾動
    driver.execute_script("window.scrollBy(0, 900);")

    charts = driver.find_element(By.CLASS_NAME,"table-body-wrapper")

    action = ActionChains(driver)
    action.move_to_element(charts).perform()

    Png = stock + ".png"
    driver.get_screenshot_as_file(Png)

    driver.close()

    img = Image.open(Png)      # 開啟圖片
    img_crop = img.crop((0,100,515,900))        # 裁切圖片
    img_crop.save(Png)

#截圖個股基本資訊
def screenshot_profile(stock):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.set_window_size(710,1000)
    stock = str(stock)
    Url = "https://tw.stock.yahoo.com/quote/" + stock + "/profile"
    driver.get(Url)

    #滾動
    driver.execute_script("window.scrollBy(0, 380);")

    Png = stock + ".png"
    driver.get_screenshot_as_file(Png)

    driver.close()

    img = Image.open(Png)      
    img_crop = img.crop((0,100,710,1000))        
    img_crop.save(Png)
    
#繪製K線圖
def plot_stcok_k_chart(stock="0050" , start='2020-01-01'):
    picname = str(stock) 
    stock = str(stock)+".TW"
    df = yf.download(stock,start)
    mpf.plot(df, type='candle', mav=(5,20), volume=True, title=stock, savefig=picname + '.png')


#繪製歷史股價
def plot_stcok_chart(stock="0050"):
    picname = str(stock) 
    stock = str(stock)+".TW"
    df = yf.download(stock)
    time.sleep(0.5)
    mpf.plot(df, type='candle', volume=True, title=stock, savefig=picname + '.png')

 #上傳至圖庫再抓下來
def imr(name):
        CLIENT_ID = "b9c0b678cf5cb2c"
        name = str(name)
        PATH =name +".png" 
        title = "Uploaded with PyImgur"

        im = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = im.upload_image(PATH, title=title)
        print(uploaded_image.title)
        print(uploaded_image.link)
        return uploaded_image.link

#刪除圖片
def delete_pic(name):
    fileTest = name + ".png"
    try:
        os.remove(fileTest)
    except OSError as e:
        print(e)
    else:
        print("File is deleted successfully")

if __name__ == "__main__":
    app.run()
