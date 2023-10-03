import sys
from stockCrawler import stockCrawler
import multiprocessing as mp
from selenium import webdriver
import random
import uuid



def title_screen():
    print("""
  /$$$$$$   /$$$$$$   /$$$$$$  /$$$$$$$  /$$$$$$$$ /$$$$$$$        /$$$$$$$   /$$$$$$  /$$$$$$$$
 /$$__  $$ /$$__  $$ /$$__  $$| $$__  $$| $$_____/| $$__  $$      | $$__  $$ /$$__  $$|__  $$__/
| $$  \__/| $$  \ $$| $$  \ $$| $$  \ $$| $$      | $$  \ $$      | $$  \ $$| $$  \ $$   | $$   
| $$ /$$$$| $$  | $$| $$  | $$| $$$$$$$ | $$$$$   | $$$$$$$/      | $$$$$$$ | $$  | $$   | $$   
| $$|_  $$| $$  | $$| $$  | $$| $$__  $$| $$__/   | $$__  $$      | $$__  $$| $$  | $$   | $$   
| $$  \ $$| $$  | $$| $$  | $$| $$  \ $$| $$      | $$  \ $$      | $$  \ $$| $$  | $$   | $$   
|  $$$$$$/|  $$$$$$/|  $$$$$$/| $$$$$$$/| $$$$$$$$| $$  | $$      | $$$$$$$/|  $$$$$$/   | $$   
 \______/  \______/  \______/ |_______/ |________/|__/  |__/      |_______/  \______/    |__/   
                                                                                                                                                                                      
""")


def initialize_useragent_list():
    ua_list = []
    with open("uastrings.txt") as f:
        for line in f:
            ua_list.append(line.strip())
    return ua_list



def initialize_products():
    products_list = []
    with open("products.txt") as f:
        for line in f:
            product_info = line.split(",")
            products_list.append(product_info)
    return products_list


def worker(crawlerObject):
    crawlerObject.run_stock_crawler()

def get_login_chromedriver():
    profile_path = "C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data\\Goober" + str(uuid.uuid4())
    driver_path = "venv/chromedriver.exe"
    uastrings = initialize_useragent_list()
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("user-data-dir=" + profile_path)
    chrome_options.add_argument('--user-agent=%s' % random.choice(uastrings))
    driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
    return driver, chrome_options

def initialize_login_session():
    home_depot_login_link = "https://www.homedepot.com/auth/view/signin"
    driver, chrome_options = get_login_chromedriver()
    driver.get(home_depot_login_link)
    user_input = input("Log in to HomeDepot, and type 'done' when logged in succesfully to continue or 'q' to quit: ")
    while user_input.lower() != "done":
        user_input = input("Try again, type 'done' when logged in succesfully to continue or 'q' to quit: ")
        if user_input.lower() == "q":
            sys.exit()
    return chrome_options

if __name__ == '__main__':
    title_screen()
    chrome_options = initialize_login_session()
    i = 1
    uastrings = initialize_useragent_list()
    products_list = initialize_products()
    list_of_objects = []
    for product_info in products_list:
        list_of_objects.append(stockCrawler(product_info, uastrings, chrome_options, i))
        i += 1
    pool = mp.Pool(mp.cpu_count() - 1)
    pool.map(worker, (crawlerObject for crawlerObject in list_of_objects))
    pool.close()
    pool.join()


