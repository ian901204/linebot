import yfinance as yf
import mplfinance as mpf
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image

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




def plot_stcok_k_chart(stock="0050" , start='2022-01-01'):
    picname = str(stock) 
    stock = str(stock)+".TW"
    df = yf.download(stock,start)
    mpf.plot(df, type='candle', style='blueskies', mav=(5,20), volume=True, title=stock, savefig=picname + '.png')



df = yf.download("0050.TW","2020-01-01")
print(df)
print(type(df))
