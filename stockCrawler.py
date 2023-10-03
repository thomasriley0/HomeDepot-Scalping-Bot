import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import time
import random
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime as d, date
import os
import zipfile
from selenium.webdriver.support import expected_conditions as EC


class stockCrawler:
    def __init__(self, product_info, uastrings, chrome_options, id):
        self.email = ""
        self.password = ""
        self.cvv = ""
        self.driver_path = "venv/chromedriver.exe"
        self.home_depot_login_link = "https://www.homedepot.com/auth/view/signin"
        self.webhook_url = ""
        self.product_link = product_info[0]
        self.storeid = product_info[1]
        self.max_quantitiy = product_info[2]
        self.id = id
        self.product_name = ""
        self.product_image_link = ""
        self.stock_status = False
        self.stock = 0
        self.uastrings = uastrings
        self.refresh_rate = random.uniform(.5, .6)
        self.chrome_options = chrome_options
        self.checkout_status = False
        self.proxies = []
        self.proxy_index = 0
        error_file = open("errors.txt", "a+")
        error_file.truncate(0)

    def run_stock_crawler(self):
        error_file = open("errors.txt", "a+")
        driver = self.get_chromedriver(use_proxy=True)
        self.selenium_request_product_link(driver, error_file)
        while not self.stock_status:
            driver.refresh()
            self.verify_product_stock(driver, error_file)
            if not self.stock_status:
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Product Link: " + self.product_link + " Item Status: Out of stock")

        print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Product Link: " + self.product_link + " Item Status: " + str(self.stock) + " Items In Stock")
        # self.send_webhook(error_file)
        driver.quit()
        self.initialize_login_session(error_file)

    def selenium_request_product_link(self, driver, error_file):
        try:
            driver.get(self.product_link)
            WebDriverWait(driver, 5).until(lambda x: x.find_element(By.ID, 'thd-helmet__script--productStructureData'))
            html = driver.page_source
            soup = BeautifulSoup(html, features="lxml")
            product_context = soup.find(id="thd-helmet__script--productStructureData").get_text()
            product_context = json.loads(product_context)
            self.product_name = product_context["name"]
            self.product_image_link = product_context["image"][0]
        except TimeoutException as e:
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while saving @context settings" + self.product_link)
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] " + "\n" + str(e))
            try:
                WebDriverWait(driver, 1).until(EC.title_contains("Access Denied"))
                driver.quit()
                self.proxy_index = self.proxy_index + 1
                self.run_stock_crawler()
            except TimeoutException:
                self.selenium_request_product_link(driver, error_file)
        except Exception as e:
            with open("errors.txt", "a") as f:
                f.write(str(e))
                f.close()
            self.selenium_request_product_link(driver, error_file)

    def verify_product_stock(self, driver, error_file):
        self.stock_status = False
        try:
            WebDriverWait(driver, 3).until(lambda x: x.find_element(By.CLASS_NAME, 'card-enabled'))
            card_buttons = driver.find_elements(by=By.CLASS_NAME, value='card-enabled')
            card_buttons[1].click()
            WebDriverWait(driver, 3).until(lambda x: x.find_element(By.XPATH, "//span[@class='u__bold u__text--success']"))
            self.stock = int((driver.find_element(by=By.XPATH, value="//span[@class='u__bold u__text--success']").text).replace(',', ''))
            self.stock_status = True
        except TimeoutException as time_err:
            WebDriverWait(driver, 1).until(EC.title_contains("Access Denied"))
            print("Here")
            driver.quit()
            self.proxy_index = self.proxy_index + 1
            self.run_stock_crawler()
        except Exception as e:
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] " + str(e))
            self.verify_product_stock(driver, error_file)

    def select_store(self, login_driver, error_file):
        print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Attempting to select store")
        login_driver.get('https://www.homedepot.com/l/')
        try:
            WebDriverWait(login_driver, 8).until(lambda x: x.find_element(By.CLASS_NAME, 'form-input__field'))
            inputField = login_driver.find_element(by=By.CLASS_NAME, value='form-input__field').send_keys(self.storeid, Keys.ENTER)
            try:
                WebDriverWait(login_driver, 3).until(lambda x: x.find_element(By.XPATH, '//*[@id="js-results"]/div[1]/div[2]/div[4]/div/button'))
            except TimeoutException as e:
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Store already selected, skipping")
                return
            button = login_driver.find_element(by=By.XPATH, value='//*[@id="js-results"]/div[1]/div[2]/div[4]/div/button')
            login_driver.execute_script("arguments[0].click();", button)
            time.sleep(self.refresh_rate)
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Store Selected Successfully")
        except TimeoutException as e:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while selecting store, retrying")
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while selecting store, retrying" + str(e))
            self.select_store(login_driver, error_file)
        except Exception as e:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while selecting store ")
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while selecting store " + str(e))

    def add_item_to_cart(self, login_driver, error_file):
        print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Attempting to add item to cart: " + self.product_link)
        login_driver.get(self.product_link)
        try:
            WebDriverWait(login_driver, 8).until(lambda x: x.find_element(By.CLASS_NAME, 'card-enabled'))
            card_buttons = login_driver.find_elements(by=By.CLASS_NAME, value='card-enabled')
            time.sleep(self.refresh_rate)
            card_buttons[1].click()
            WebDriverWait(login_driver, 8).until(lambda x: x.find_element(By.XPATH, '//*[@id="root"]/div/div[3]/div/div/div[3]/div/div/div[10]/div/div/div[2]/div/div/div[2]/div[1]/div/div/button'))
            time.sleep(self.refresh_rate)
            atc_button = login_driver.find_element(by=By.XPATH, value='//*[@id="root"]/div/div[3]/div/div/div[3]/div/div/div[10]/div/div/div[2]/div/div/div[2]/div[1]/div/div/button')
            login_driver.execute_script("arguments[0].click();", atc_button)
            try:
                time.sleep(3)
                login_driver.switch_to.frame(login_driver.find_element(by=By.CLASS_NAME, value="thd-drawer_frame"))
                WebDriverWait(login_driver, 4).until(lambda x: x.find_element(By.CLASS_NAME, 'alert-inline--success'))
                login_driver.switch_to.default_content()
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Item successfully added to cart: " + self.product_link)
            except NoSuchElementException as e:
                login_driver.switch_to.default_content()
                print(e)
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] No element found Error adding item to cart, retrying " + self.product_link)
                error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while adding item to cart, retrying" + self.product_link + str(e))
                self.add_item_to_cart(login_driver, error_file)
        except TimeoutException as time_err:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while adding item to cart, retrying" + self.product_link)
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while adding item to cart, retrying" + self.product_link + str(time_err))
            self.add_item_to_cart(login_driver, error_file)
        except Exception as e:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while adding item to cart " + self.product_link)
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while adding item to cart " + self.product_link + str(e))

    def initialize_login_session(self, error_file):
        login_driver = webdriver.Chrome(self.driver_path, chrome_options=self.chrome_options)
        login_driver.get("https://www.homedepot.com/")
        try:
            WebDriverWait(login_driver, 3).until(lambda x: x.find_element(By.XPATH, '//*[@id="recentOrderHistory-php-hydrator"]/div/div[2]/div/a'))
            sign_in_btn = login_driver.find_element(by=By.XPATH, value='//*[@id="recentOrderHistory-php-hydrator"]/div/div[2]/div/a')
            login_driver.execute_script("arguments[0].click();", sign_in_btn)
            WebDriverWait(login_driver, 10).until(lambda x: x.find_element(By.ID, 'username'))
            time.sleep(self.refresh_rate)
            login_driver.findElement(by=By.ID, value='username').send_keys(Keys.ENTER)
            WebDriverWait(login_driver, 10).until(lambda x: x.find_element(By.ID, 'password-input-field'))
            time.sleep(self.refresh_rate)
            login_driver.find_element(by=By.ID, value='password-input-field').send_keys(self.password, Keys.ENTER)
            time.sleep(self.refresh_rate)
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Account session active")
            self.checkout(login_driver, error_file)
            return
        except TimeoutException as e:
            pass
        except Exception as e:
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while logging in continuing session" + str(e))
        try:
            WebDriverWait(login_driver, 1).until(lambda x: x.find_element(By.CLASS_NAME, 'message-text--1khrs'))
            #logged in
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Account session active")
            self.checkout(login_driver, error_file)
        except TimeoutException as time_err:
            #logged out
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Account session inactive")
            #self.log_in(login_driver, error_file)
            self.checkout(login_driver, error_file)
        except Exception as e:
            print(("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error in initialize_login_session" + self.product_link + str(e)))
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error in initialize_login_session" + self.product_link + str(e))

    def log_in(self, login_driver, error_file):
        print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Attempting to login")
        try:
            login_driver.get(self.home_depot_login_link)
            WebDriverWait(login_driver, 8).until(lambda x: x.find_element(By.XPATH, '//*[@id="username"]'))
            time.sleep(self.refresh_rate)
            login_driver.find_element(by=By.XPATH, value='//*[@id="username"]').send_keys(self.email, Keys.ENTER)
            WebDriverWait(login_driver, 8).until(lambda x: x.find_element(By.XPATH, '//*[@id="password-input-field"]'))
            time.sleep(self.refresh_rate)
            login_driver.find_element(by=By.XPATH, value='//*[@id="password-input-field"]').send_keys(self.password, Keys.ENTER)
            time.sleep(4)
            login_driver.get("https://www.homedepot.com/")
            try:
                WebDriverWait(login_driver, 5).until(lambda x: x.find_element(By.CLASS_NAME, 'message-text--1khrs'))
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Login sucessful")

            except TimeoutException as time_err:
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Login failure")
                error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Login failure" + str(time_err))
                self.log_in(login_driver, error_file)

        except TimeoutException as time_err:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while logging in, retrying")
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while logging in, retrying" + str(time_err))
            self.log_in(login_driver)

        except Exception as e:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error logging in")
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error logging in" + str(e))

    def checkout(self, login_driver, error_file):
        print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Attempting to checkout: " + self.product_link)
        self.select_store(login_driver, error_file)
        self.add_item_to_cart(login_driver, error_file)
        try:
            login_driver.get("https://www.homedepot.com/mycart/home")
            WebDriverWait(login_driver, 5).until(lambda x: x.find_element(By.CLASS_NAME, "cartItem__qtyInput"))
            quantity_input = login_driver.find_element(by=By.CLASS_NAME, value="cartItem__qtyInput")
            for i in range(1, 4):
                quantity_input.send_keys(Keys.BACKSPACE)
            if self.stock >= int(self.max_quantitiy):
                quantity_input.send_keys(self.max_quantitiy, Keys.TAB)
                print(("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Quantitiy succesfully changed"))
            else:
                quantity_input.clear().send_keys(self.stock, Keys.TAB)
                print(("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Quantitiy succesfully changed"))
            time.sleep(self.refresh_rate)
            login_driver.get("https://www.homedepot.com/mycheckout/checkout")
            try:
                WebDriverWait(login_driver, 1).until(lambda x: x.find_element(By.CLASS_NAME, 'u__m-left-normal'))
                continue_button = login_driver.find_element(by=By.CLASS_NAME, value='u__m-left-normal')
                login_driver.execute_script("arguments[0].click();", continue_button)

            except TimeoutException:
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Skipping reccomended address button handling" + self.product_link)

            WebDriverWait(login_driver, 5).until(lambda x: x.find_element(By.CLASS_NAME, 'form-input__field'))
            cvv_input = login_driver.find_element(by=By.CLASS_NAME, value='form-input__field').send_keys(self.cvv, Keys.TAB)
            WebDriverWait(login_driver, 5).until(lambda x: x.find_element(By.NAME, 'placeOrderButton'))
            place_order_button = login_driver.find_element(by=By.NAME, value='placeOrderButton')
            login_driver.execute_script("arguments[0].click();", place_order_button)
            try:
                WebDriverWait(login_driver, 20).until(EC.title_contains("Order Confirmation"))
                self.checkout_status = True
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str( self.id) + "] Checkout Successful")
                self.send_webhook(error_file)
            except TimeoutException as time_err:
                print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str( self.id) + "] Timeout error while checking if checkout is complete, retrying")
                error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str( self.id) + "] Timeout error while checking if checkout is complete, retrying" + str(time_err))
        except TimeoutException as time_err:
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while checking out, retrying" )
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Timeout error while checking out, retrying" + str(time_err))
            self.checkout(login_driver, error_file)

        except Exception as e:
            print(e)
            print("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while checking out")
            error_file.write("[" + d.now().strftime("%Y-%m-%d %H:%M:%S") + "]" + " [" + "Task ID: " + str(self.id) + "] Fatal error while checking out" + str(e))

    def send_webhook(self, error_file):
        try:
            webhook = DiscordWebhook(url=self.webhook_url)
            embed = DiscordEmbed(title=self.product_name, color=242424)
            embed.set_author(name='GooberNotifcations')
            embed.set_thumbnail(url=self.product_image_link)
            if self.checkout_status:
                embed.add_embed_field(name='Checkout Status', value="Successful")
                if self.stock >= int(self.max_quantitiy):
                    embed.add_embed_field(name='Quantity', value=self.max_quantitiy)
                else:
                    embed.add_embed_field(name='Quantity', value=self.stock)
            else:
                embed.add_embed_field(name='Stock', value=self.stock)
            embed.add_embed_field(name='Link', value=self.product_link)
            embed.set_footer(text='GooberNotifs v.1.0')
            embed.set_timestamp()
            webhook.add_embed(embed)
            response = webhook.execute()
        except Exception as e:
            error_file.write(str(e))

    def initialize_driver_options(self):
        PROXY_HOST = self.proxies[0][self.proxy_index]
        PROXY_PORT = self.proxies[1][self.proxy_index]
        PROXY_USER = 'leaf'  # username
        PROXY_PASS = 'Hze5HN7B'  # password

        manifest_json = """
          {
              "version": "1.0.0",
              "manifest_version": 2,
              "name": "Chrome Proxy",
              "permissions": [
                  "proxy",
                  "tabs",
                  "unlimitedStorage",
                  "storage",
                  "<all_urls>",
                  "webRequest",
                  "webRequestBlocking"
              ],
              "background": {
                  "scripts": ["background.js"]
              },
              "minimum_chrome_version":"22.0.0"
          }
          """

        background_js = """
          var config = {
                  mode: "fixed_servers",
                  rules: {
                  singleProxy: {
                      scheme: "http",
                      host: "%s",
                      port: parseInt(%s)
                  },
                  bypassList: ["localhost"]
                  }
              };

          chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

          function callbackFn(details) {
              return {
                  authCredentials: {
                      username: "%s",
                      password: "%s"
                  }
              };
          }

          chrome.webRequest.onAuthRequired.addListener(
                      callbackFn,
                      {urls: ["<all_urls>"]},
                      ['blocking']
          );
          """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)

        return manifest_json, background_js

    def get_chromedriver(self, use_proxy=True):
        manifest_json, background_js = self.initialize_driver_options()
        path = os.path.dirname(os.path.abspath(__file__))
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option(
            'prefs',
            {
                'profile.managed_default_content_settings.images': 2,
            }
        )
        if use_proxy:
            pluginfile = 'proxy_auth_plugin.zip'
            with zipfile.ZipFile(pluginfile, 'w') as zp:
                zp.writestr("manifest.json", manifest_json)
                zp.writestr("background.js", background_js)
            chrome_options.add_extension(pluginfile)
        chrome_options.add_argument('--user-agent=%s' % random.choice(self.uastrings))
        driver = webdriver.Chrome(os.path.join(path, self.driver_path), chrome_options=chrome_options)
        return driver





