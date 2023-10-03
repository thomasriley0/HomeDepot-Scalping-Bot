# Home-Depot-Scalping-Bot
What it is:

This is a selenium based script coded in python to monitor the stock of a specific product and automatically purchase the desired quantity when the product is in stock. The module works by opening a selenium window and navigating to the HomeDepot website where the user can manually log into their account. After logging in, type 'done' in the terminal & the bot will now begin working fully automatically.

How it works:

In products.txt each line contains the following: link,store id, quantity. (example: https://www.homedepot.com/p/204836075,4415,1) Each of these lines specifies a product that will be monitored automatically by the bot, which store id to switch to when purchasing the product & what quantity of the product should be purchase.

In UAStrings.txt we can specify a User Agent string on each line that will be randomolly rotated to for each browser.

In errors.txt, any exceptions or errors that occur are logged in this file. It is useful for debugging and seeing fatal errors.

In main.py, this includes initialization functions and main function which will first call initialize_login_session(), to intialize the session cookies for the selenium browser so that we can import our HomeDepot account session. We then call initialize_useragent_list(), to intialize an array containing all the UAStrings. Then we call initialize_products(), to initalize a list containing all the products, store id for the product and the quantity for the product. For each of the given products, we utiliaze multiprocessing to launch a selenium browser in tandemn. 

In stockCrawler.py, this includes a class StockCrawler which contains all the given states for the bot, i.e driver paths, webook url, product links, storeids, quantities, id, product_names etc. This file also contains functions to navigate to the specific product url via selenium & extract the stock status, if it is out of stock efresh every second or so, when it comes into stock then send the discord webook and call the checkout product function. The checkout produt function will change to the specific store id, naviate to the product, add the specified amount to the cart or the maximium amount possible. Then it will checkout the items in the cart and send a webhook with the success to a discord server.

This is a working example of the bot (blurred out sensitive information): 

https://github.com/thomasriley0/Home-Depot-Scalping-Bot/assets/129229020/ce4425c3-0cbe-484c-90a2-763596151ee5



This is an example of the discord webhook outputs: 

<img width="596" alt="Screenshot 2023-10-03 at 4 31 48 PM" src="https://github.com/thomasriley0/Home-Depot-Scalping-Bot/assets/129229020/f5eb9cba-4304-4936-bdd6-5d6205cce090">



