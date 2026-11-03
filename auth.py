import os
import robin_stocks.robinhood as rh
from dotenv import load_dotenv

load_dotenv()

def login():
    username = os.environ["ROBINHOOD_USERNAME"]
    password = os.environ["ROBINHOOD_PASSWORD"]
    rh.login(username, password)
    print("Logged in to Robinhood.")

def logout():
    rh.logout()
    print("Logged out.")
