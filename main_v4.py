import logging
import logging.handlers
import sys
import time
import datetime
import json
import numpy as np
from binance.client import Client
from web3 import Web3
from time import sleep
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import math
import csv
from web3 import Web3
from web3.datastructures import AttributeDict
from hexbytes import HexBytes
from decimal import Decimal, ROUND_FLOOR
import traceback
import pytz
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


# ONly make global if we want them to be modifies by any function else it doesnt cause any issues when called from inside a function
global leverage, threshold_balance, number_of_try, proxy_contract ,alchemy_url, percent_we_can_loose_stop_loss, ABI , traders_list, trading_data_df_path, dex_name, receiver_email, trading_data_df_length_stored, last_email_sent_date



# EMail password for mail service. Use this to generate password for an app (https://myaccount.google.com/apppasswords).
sender_email = "chetantiwaridgp5@gmail.com"
email_password = "cwou aqhs oupi hcbj"



# Google sheets 
credentials_file ={
#
}


# Specify the ID of the Google Sheet    
sheet_id = "1pi-7rD821gSnGCZPZEbgvrH252yXqhcg5ULOo19Hnp8"
google_sheet_url = "https://docs.google.com/spreadsheets/d/1pi-7rD821gSnGCZPZEbgvrH252yXqhcg5ULOo19Hnp8/edit?usp=sharing"
# https://www.youtube.com/watch?v=zCEJurLGFRk&t=1318s   Refer to this video in future if needed for google sheet api operations in gspread operations


# Specify the ID of scraper bot's Google Sheet
SHEET_ID = "1OrdYgehZxStX6tPTJZnxQ5zFtmK8FcY_S_Ey1XwLcd4"
SHEET_NAME = "GMXNEWBOT"


# Email IDs
receiver_email = ["saamisajidwork@gmail.com"] #'chetantiwaridgp5@gmail.com', 'sainath@primetrade.ai'



# Naming the decenteralized exchange
dex_name = ["GMXV2"]
DEX = ["GMXV2"]


# Initialize an empty list to store dictionaries
ban_positions_info_list = []


our_leverage = 10 # This is the binance leverage we use, make sure it is same for each file.

max_leverage_for_stop_price = 150 # This is extreme case (150) on the exchange for the tokens.
min_leverage_for_stop_price = 2 # This is our choice. Note: Make sure it is never less than or equal to 1, as stop price will become 0.

threshold_balance = 50 # Keep it at 8% of the available balance
investement_risk_factor = 1
number_of_try = 4    # will try number_of_try-1 times when placing each order if exception occours.
percent_we_can_loose_stop_loss = 0.2 #Ratio of how much we are ready to loose of our colletral
profit_percent = 0.02 #Amount ratio we want to gain      
price_difference_ratio = 0.80 # ratio for price difference deviation allowed from alchemy price : binance price
retry_time = 1 # retry time for trading in seconds
ban_time_hours = 48 # Ban time for postions which had exceptions because they returned some code instead of "True".
trading_data_df_length_stored = 0 # Trading_data_df_length_stored initially zero
last_email_sent_date = None # Summary email sent date, initiated as none
summary_sending_hour = 18 #  The time at which summary email is sent in every 24 hrs (24 hrs format)


proxy_contract = '0xc8ee91a54287db53897056e12d9819156d3822fb'
pair_proxy_address = "0x5Ca84c34a381434786738735265b9f3FD814b824"

alchemy_url = "https://arb-mainnet.g.alchemy.com/v2/nVhd7pQrSuvgbJE2HsB248DNd3XepeaA" 



stop_signal_path = f"{dex_name[0]}_stop_signal.txt"
# keep stop_signal = "" or Keep it as stop_signal = "STOP"


# Load the top 100 traders list from the CSV file
traders_list = pd.read_csv("Top_traders_gmxv2_rank_15-11-2024.csv")


# Path to the trading_data_df
trading_data_df_path = f"{dex_name[0]}_trading_data_df.csv"



# Test Net id and password
# forextraworksid@gmail.com
# S#H4LUR2q6P&#/z          




# Creating stop singal file
with open(stop_signal_path, "w") as f:
    print(f"Created {stop_signal_path}")




    #### DF initiator



# Initiating dataframe to manage all trades
trading_data_df = pd.DataFrame(columns=[
            'time', 
            'trade_order_id', 
            'address', 
            'symbol', 
            'is_long_short', 
            'trade_type',
            'leads_price',
            'price', 
            'weighted_score_ratio',
            'leads_max_volume',
            'leads_leverage',
            'leads_transaction_quantity', 
            'leads_transaction_amount', 
            'our_leverage',
            'our_transaction_quantity', 
            'our_transaction_amount', 
            'leads_total_hold', 
            'leads_total_investment',
            'avg_leads_coin_price',
            'our_total_hold', 
            'our_total_investment',
            'avg_coin_price', 
            'total_hold_ratio', 
            'stop_loss_price', 
            'stop_loss_order_id', 
            'is_stop_loss_executed',
            'is_liquidated', 
            'take_profit_price', 
            'take_profit_order_id', 
            'PNL',
            'DEX',
            'available_balance'])


ABI = json.loads('[{"inputs":[{"internalType":"contract RoleStore","name":"_roleStore","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"address","name":"msgSender","type":"address"},{"internalType":"string","name":"role","type":"string"}],"name":"Unauthorized","type":"error"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"msgSender","type":"address"},{"indexed":false,"internalType":"string","name":"eventName","type":"string"},{"indexed":true,"internalType":"string","name":"eventNameHash","type":"string"},{"components":[{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address","name":"value","type":"address"}],"internalType":"struct EventUtils.AddressKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address[]","name":"value","type":"address[]"}],"internalType":"struct EventUtils.AddressArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.AddressItems","name":"addressItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct EventUtils.UintKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256[]","name":"value","type":"uint256[]"}],"internalType":"struct EventUtils.UintArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.UintItems","name":"uintItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256","name":"value","type":"int256"}],"internalType":"struct EventUtils.IntKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256[]","name":"value","type":"int256[]"}],"internalType":"struct EventUtils.IntArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.IntItems","name":"intItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool","name":"value","type":"bool"}],"internalType":"struct EventUtils.BoolKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool[]","name":"value","type":"bool[]"}],"internalType":"struct EventUtils.BoolArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BoolItems","name":"boolItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32","name":"value","type":"bytes32"}],"internalType":"struct EventUtils.Bytes32KeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32[]","name":"value","type":"bytes32[]"}],"internalType":"struct EventUtils.Bytes32ArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.Bytes32Items","name":"bytes32Items","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes","name":"value","type":"bytes"}],"internalType":"struct EventUtils.BytesKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes[]","name":"value","type":"bytes[]"}],"internalType":"struct EventUtils.BytesArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BytesItems","name":"bytesItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string","name":"value","type":"string"}],"internalType":"struct EventUtils.StringKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string[]","name":"value","type":"string[]"}],"internalType":"struct EventUtils.StringArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.StringItems","name":"stringItems","type":"tuple"}],"indexed":false,"internalType":"struct EventUtils.EventLogData","name":"eventData","type":"tuple"}],"name":"EventLog","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"msgSender","type":"address"},{"indexed":false,"internalType":"string","name":"eventName","type":"string"},{"indexed":true,"internalType":"string","name":"eventNameHash","type":"string"},{"indexed":true,"internalType":"bytes32","name":"topic1","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address","name":"value","type":"address"}],"internalType":"struct EventUtils.AddressKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address[]","name":"value","type":"address[]"}],"internalType":"struct EventUtils.AddressArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.AddressItems","name":"addressItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct EventUtils.UintKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256[]","name":"value","type":"uint256[]"}],"internalType":"struct EventUtils.UintArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.UintItems","name":"uintItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256","name":"value","type":"int256"}],"internalType":"struct EventUtils.IntKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256[]","name":"value","type":"int256[]"}],"internalType":"struct EventUtils.IntArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.IntItems","name":"intItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool","name":"value","type":"bool"}],"internalType":"struct EventUtils.BoolKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool[]","name":"value","type":"bool[]"}],"internalType":"struct EventUtils.BoolArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BoolItems","name":"boolItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32","name":"value","type":"bytes32"}],"internalType":"struct EventUtils.Bytes32KeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32[]","name":"value","type":"bytes32[]"}],"internalType":"struct EventUtils.Bytes32ArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.Bytes32Items","name":"bytes32Items","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes","name":"value","type":"bytes"}],"internalType":"struct EventUtils.BytesKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes[]","name":"value","type":"bytes[]"}],"internalType":"struct EventUtils.BytesArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BytesItems","name":"bytesItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string","name":"value","type":"string"}],"internalType":"struct EventUtils.StringKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string[]","name":"value","type":"string[]"}],"internalType":"struct EventUtils.StringArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.StringItems","name":"stringItems","type":"tuple"}],"indexed":false,"internalType":"struct EventUtils.EventLogData","name":"eventData","type":"tuple"}],"name":"EventLog1","type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"address","name":"msgSender","type":"address"},{"indexed":false,"internalType":"string","name":"eventName","type":"string"},{"indexed":true,"internalType":"string","name":"eventNameHash","type":"string"},{"indexed":true,"internalType":"bytes32","name":"topic1","type":"bytes32"},{"indexed":true,"internalType":"bytes32","name":"topic2","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address","name":"value","type":"address"}],"internalType":"struct EventUtils.AddressKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address[]","name":"value","type":"address[]"}],"internalType":"struct EventUtils.AddressArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.AddressItems","name":"addressItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct EventUtils.UintKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256[]","name":"value","type":"uint256[]"}],"internalType":"struct EventUtils.UintArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.UintItems","name":"uintItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256","name":"value","type":"int256"}],"internalType":"struct EventUtils.IntKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256[]","name":"value","type":"int256[]"}],"internalType":"struct EventUtils.IntArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.IntItems","name":"intItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool","name":"value","type":"bool"}],"internalType":"struct EventUtils.BoolKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool[]","name":"value","type":"bool[]"}],"internalType":"struct EventUtils.BoolArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BoolItems","name":"boolItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32","name":"value","type":"bytes32"}],"internalType":"struct EventUtils.Bytes32KeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32[]","name":"value","type":"bytes32[]"}],"internalType":"struct EventUtils.Bytes32ArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.Bytes32Items","name":"bytes32Items","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes","name":"value","type":"bytes"}],"internalType":"struct EventUtils.BytesKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes[]","name":"value","type":"bytes[]"}],"internalType":"struct EventUtils.BytesArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BytesItems","name":"bytesItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string","name":"value","type":"string"}],"internalType":"struct EventUtils.StringKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string[]","name":"value","type":"string[]"}],"internalType":"struct EventUtils.StringArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.StringItems","name":"stringItems","type":"tuple"}],"indexed":false,"internalType":"struct EventUtils.EventLogData","name":"eventData","type":"tuple"}],"name":"EventLog2","type":"event"},{"inputs":[{"internalType":"bytes32","name":"topic1","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"emitDataLog1","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"topic1","type":"bytes32"},{"internalType":"bytes32","name":"topic2","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"emitDataLog2","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"topic1","type":"bytes32"},{"internalType":"bytes32","name":"topic2","type":"bytes32"},{"internalType":"bytes32","name":"topic3","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"emitDataLog3","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes32","name":"topic1","type":"bytes32"},{"internalType":"bytes32","name":"topic2","type":"bytes32"},{"internalType":"bytes32","name":"topic3","type":"bytes32"},{"internalType":"bytes32","name":"topic4","type":"bytes32"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"emitDataLog4","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"eventName","type":"string"},{"components":[{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address","name":"value","type":"address"}],"internalType":"struct EventUtils.AddressKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address[]","name":"value","type":"address[]"}],"internalType":"struct EventUtils.AddressArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.AddressItems","name":"addressItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct EventUtils.UintKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256[]","name":"value","type":"uint256[]"}],"internalType":"struct EventUtils.UintArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.UintItems","name":"uintItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256","name":"value","type":"int256"}],"internalType":"struct EventUtils.IntKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256[]","name":"value","type":"int256[]"}],"internalType":"struct EventUtils.IntArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.IntItems","name":"intItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool","name":"value","type":"bool"}],"internalType":"struct EventUtils.BoolKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool[]","name":"value","type":"bool[]"}],"internalType":"struct EventUtils.BoolArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BoolItems","name":"boolItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32","name":"value","type":"bytes32"}],"internalType":"struct EventUtils.Bytes32KeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32[]","name":"value","type":"bytes32[]"}],"internalType":"struct EventUtils.Bytes32ArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.Bytes32Items","name":"bytes32Items","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes","name":"value","type":"bytes"}],"internalType":"struct EventUtils.BytesKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes[]","name":"value","type":"bytes[]"}],"internalType":"struct EventUtils.BytesArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BytesItems","name":"bytesItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string","name":"value","type":"string"}],"internalType":"struct EventUtils.StringKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string[]","name":"value","type":"string[]"}],"internalType":"struct EventUtils.StringArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.StringItems","name":"stringItems","type":"tuple"}],"internalType":"struct EventUtils.EventLogData","name":"eventData","type":"tuple"}],"name":"emitEventLog","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"eventName","type":"string"},{"internalType":"bytes32","name":"topic1","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address","name":"value","type":"address"}],"internalType":"struct EventUtils.AddressKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address[]","name":"value","type":"address[]"}],"internalType":"struct EventUtils.AddressArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.AddressItems","name":"addressItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct EventUtils.UintKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256[]","name":"value","type":"uint256[]"}],"internalType":"struct EventUtils.UintArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.UintItems","name":"uintItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256","name":"value","type":"int256"}],"internalType":"struct EventUtils.IntKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256[]","name":"value","type":"int256[]"}],"internalType":"struct EventUtils.IntArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.IntItems","name":"intItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool","name":"value","type":"bool"}],"internalType":"struct EventUtils.BoolKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool[]","name":"value","type":"bool[]"}],"internalType":"struct EventUtils.BoolArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BoolItems","name":"boolItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32","name":"value","type":"bytes32"}],"internalType":"struct EventUtils.Bytes32KeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32[]","name":"value","type":"bytes32[]"}],"internalType":"struct EventUtils.Bytes32ArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.Bytes32Items","name":"bytes32Items","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes","name":"value","type":"bytes"}],"internalType":"struct EventUtils.BytesKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes[]","name":"value","type":"bytes[]"}],"internalType":"struct EventUtils.BytesArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BytesItems","name":"bytesItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string","name":"value","type":"string"}],"internalType":"struct EventUtils.StringKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string[]","name":"value","type":"string[]"}],"internalType":"struct EventUtils.StringArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.StringItems","name":"stringItems","type":"tuple"}],"internalType":"struct EventUtils.EventLogData","name":"eventData","type":"tuple"}],"name":"emitEventLog1","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"eventName","type":"string"},{"internalType":"bytes32","name":"topic1","type":"bytes32"},{"internalType":"bytes32","name":"topic2","type":"bytes32"},{"components":[{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address","name":"value","type":"address"}],"internalType":"struct EventUtils.AddressKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"address[]","name":"value","type":"address[]"}],"internalType":"struct EventUtils.AddressArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.AddressItems","name":"addressItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256","name":"value","type":"uint256"}],"internalType":"struct EventUtils.UintKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"uint256[]","name":"value","type":"uint256[]"}],"internalType":"struct EventUtils.UintArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.UintItems","name":"uintItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256","name":"value","type":"int256"}],"internalType":"struct EventUtils.IntKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"int256[]","name":"value","type":"int256[]"}],"internalType":"struct EventUtils.IntArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.IntItems","name":"intItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool","name":"value","type":"bool"}],"internalType":"struct EventUtils.BoolKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bool[]","name":"value","type":"bool[]"}],"internalType":"struct EventUtils.BoolArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BoolItems","name":"boolItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32","name":"value","type":"bytes32"}],"internalType":"struct EventUtils.Bytes32KeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes32[]","name":"value","type":"bytes32[]"}],"internalType":"struct EventUtils.Bytes32ArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.Bytes32Items","name":"bytes32Items","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes","name":"value","type":"bytes"}],"internalType":"struct EventUtils.BytesKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"bytes[]","name":"value","type":"bytes[]"}],"internalType":"struct EventUtils.BytesArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.BytesItems","name":"bytesItems","type":"tuple"},{"components":[{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string","name":"value","type":"string"}],"internalType":"struct EventUtils.StringKeyValue[]","name":"items","type":"tuple[]"},{"components":[{"internalType":"string","name":"key","type":"string"},{"internalType":"string[]","name":"value","type":"string[]"}],"internalType":"struct EventUtils.StringArrayKeyValue[]","name":"arrayItems","type":"tuple[]"}],"internalType":"struct EventUtils.StringItems","name":"stringItems","type":"tuple"}],"internalType":"struct EventUtils.EventLogData","name":"eventData","type":"tuple"}],"name":"emitEventLog2","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"roleStore","outputs":[{"internalType":"contract RoleStore","name":"","type":"address"}],"stateMutability":"view","type":"function"}]')


ABIs = json.loads('[{"inputs": [{"internalType": "address", "name": "market", "type": "address"}], "name": "DisabledMarket", "type": "error"}, {"inputs": [], "name": "EmptyMarket", "type": "error"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "account", "type": "address"}, {"internalType": "uint256", "name": "start", "type": "uint256"}, {"internalType": "uint256", "name": "end", "type": "uint256"}], "name": "getAccountOrders", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "callbackContract", "type": "address"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "initialCollateralToken", "type": "address"}, {"internalType": "address[]", "name": "swapPath", "type": "address[]"}], "internalType": "struct Order.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "enum Order.OrderType", "name": "orderType", "type": "uint8"}, {"internalType": "enum Order.DecreasePositionSwapType", "name": "decreasePositionSwapType", "type": "uint8"}, {"internalType": "uint256", "name": "sizeDeltaUsd", "type": "uint256"}, {"internalType": "uint256", "name": "initialCollateralDeltaAmount", "type": "uint256"}, {"internalType": "uint256", "name": "triggerPrice", "type": "uint256"}, {"internalType": "uint256", "name": "acceptablePrice", "type": "uint256"}, {"internalType": "uint256", "name": "executionFee", "type": "uint256"}, {"internalType": "uint256", "name": "callbackGasLimit", "type": "uint256"}, {"internalType": "uint256", "name": "minOutputAmount", "type": "uint256"}, {"internalType": "uint256", "name": "updatedAtBlock", "type": "uint256"}], "internalType": "struct Order.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "isLong", "type": "bool"}, {"internalType": "bool", "name": "shouldUnwrapNativeToken", "type": "bool"}, {"internalType": "bool", "name": "isFrozen", "type": "bool"}], "internalType": "struct Order.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Order.Props[]", "name": "", "type": "tuple[]"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "contract IReferralStorage", "name": "referralStorage", "type": "address"}, {"internalType": "bytes32[]", "name": "positionKeys", "type": "bytes32[]"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices[]", "name": "prices", "type": "tuple[]"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}], "name": "getAccountPositionInfoList", "outputs": [{"components": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "collateralToken", "type": "address"}], "internalType": "struct Position.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "sizeInUsd", "type": "uint256"}, {"internalType": "uint256", "name": "sizeInTokens", "type": "uint256"}, {"internalType": "uint256", "name": "collateralAmount", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFactor", "type": "uint256"}, {"internalType": "uint256", "name": "fundingFeeAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "longTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "increasedAtBlock", "type": "uint256"}, {"internalType": "uint256", "name": "decreasedAtBlock", "type": "uint256"}], "internalType": "struct Position.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "isLong", "type": "bool"}], "internalType": "struct Position.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Position.Props", "name": "position", "type": "tuple"}, {"components": [{"components": [{"internalType": "bytes32", "name": "referralCode", "type": "bytes32"}, {"internalType": "address", "name": "affiliate", "type": "address"}, {"internalType": "address", "name": "trader", "type": "address"}, {"internalType": "uint256", "name": "totalRebateFactor", "type": "uint256"}, {"internalType": "uint256", "name": "traderDiscountFactor", "type": "uint256"}, {"internalType": "uint256", "name": "totalRebateAmount", "type": "uint256"}, {"internalType": "uint256", "name": "traderDiscountAmount", "type": "uint256"}, {"internalType": "uint256", "name": "affiliateRewardAmount", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionReferralFees", "name": "referral", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "fundingFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "claimableLongTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "claimableShortTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "latestFundingFeeAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "latestLongTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "latestShortTokenClaimableFundingAmountPerSize", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionFundingFees", "name": "funding", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "borrowingFeeUsd", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeeAmountForFeeReceiver", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionBorrowingFees", "name": "borrowing", "type": "tuple"}, {"components": [{"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "uint256", "name": "uiFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "uiFeeAmount", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionUiFees", "name": "ui", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "collateralTokenPrice", "type": "tuple"}, {"internalType": "uint256", "name": "positionFeeFactor", "type": "uint256"}, {"internalType": "uint256", "name": "protocolFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "positionFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "feeReceiverAmount", "type": "uint256"}, {"internalType": "uint256", "name": "feeAmountForPool", "type": "uint256"}, {"internalType": "uint256", "name": "positionFeeAmountForPool", "type": "uint256"}, {"internalType": "uint256", "name": "positionFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "totalCostAmountExcludingFunding", "type": "uint256"}, {"internalType": "uint256", "name": "totalCostAmount", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionFees", "name": "fees", "type": "tuple"}, {"components": [{"internalType": "int256", "name": "priceImpactUsd", "type": "int256"}, {"internalType": "uint256", "name": "priceImpactDiffUsd", "type": "uint256"}, {"internalType": "uint256", "name": "executionPrice", "type": "uint256"}], "internalType": "struct ReaderPricingUtils.ExecutionPriceResult", "name": "executionPriceResult", "type": "tuple"}, {"internalType": "int256", "name": "basePnlUsd", "type": "int256"}, {"internalType": "int256", "name": "uncappedBasePnlUsd", "type": "int256"}, {"internalType": "int256", "name": "pnlAfterPriceImpactUsd", "type": "int256"}], "internalType": "struct ReaderUtils.PositionInfo[]", "name": "", "type": "tuple[]"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "account", "type": "address"}, {"internalType": "uint256", "name": "start", "type": "uint256"}, {"internalType": "uint256", "name": "end", "type": "uint256"}], "name": "getAccountPositions", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "collateralToken", "type": "address"}], "internalType": "struct Position.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "sizeInUsd", "type": "uint256"}, {"internalType": "uint256", "name": "sizeInTokens", "type": "uint256"}, {"internalType": "uint256", "name": "collateralAmount", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFactor", "type": "uint256"}, {"internalType": "uint256", "name": "fundingFeeAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "longTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "increasedAtBlock", "type": "uint256"}, {"internalType": "uint256", "name": "decreasedAtBlock", "type": "uint256"}], "internalType": "struct Position.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "isLong", "type": "bool"}], "internalType": "struct Position.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Position.Props[]", "name": "", "type": "tuple[]"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "bool", "name": "isLong", "type": "bool"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}], "name": "getAdlState", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "bool", "name": "", "type": "bool"}, {"internalType": "int256", "name": "", "type": "int256"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "bytes32", "name": "key", "type": "bytes32"}], "name": "getDeposit", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "callbackContract", "type": "address"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "initialLongToken", "type": "address"}, {"internalType": "address", "name": "initialShortToken", "type": "address"}, {"internalType": "address[]", "name": "longTokenSwapPath", "type": "address[]"}, {"internalType": "address[]", "name": "shortTokenSwapPath", "type": "address[]"}], "internalType": "struct Deposit.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "initialLongTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "initialShortTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "minMarketTokens", "type": "uint256"}, {"internalType": "uint256", "name": "updatedAtBlock", "type": "uint256"}, {"internalType": "uint256", "name": "executionFee", "type": "uint256"}, {"internalType": "uint256", "name": "callbackGasLimit", "type": "uint256"}], "internalType": "struct Deposit.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "shouldUnwrapNativeToken", "type": "bool"}], "internalType": "struct Deposit.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Deposit.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "uint256", "name": "longTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenAmount", "type": "uint256"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}], "name": "getDepositAmountOut", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "marketKey", "type": "address"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"internalType": "uint256", "name": "positionSizeInUsd", "type": "uint256"}, {"internalType": "uint256", "name": "positionSizeInTokens", "type": "uint256"}, {"internalType": "int256", "name": "sizeDeltaUsd", "type": "int256"}, {"internalType": "bool", "name": "isLong", "type": "bool"}], "name": "getExecutionPrice", "outputs": [{"components": [{"internalType": "int256", "name": "priceImpactUsd", "type": "int256"}, {"internalType": "uint256", "name": "priceImpactDiffUsd", "type": "uint256"}, {"internalType": "uint256", "name": "executionPrice", "type": "uint256"}], "internalType": "struct ReaderPricingUtils.ExecutionPriceResult", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "key", "type": "address"}], "name": "getMarket", "outputs": [{"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "bytes32", "name": "salt", "type": "bytes32"}], "name": "getMarketBySalt", "outputs": [{"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "address", "name": "marketKey", "type": "address"}], "name": "getMarketInfo", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"internalType": "uint256", "name": "borrowingFactorPerSecondForLongs", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFactorPerSecondForShorts", "type": "uint256"}, {"components": [{"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "fundingFeeAmountPerSize", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "claimableFundingAmountPerSize", "type": "tuple"}], "internalType": "struct ReaderUtils.BaseFundingValues", "name": "baseFunding", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "longsPayShorts", "type": "bool"}, {"internalType": "uint256", "name": "fundingFactorPerSecond", "type": "uint256"}, {"internalType": "int256", "name": "nextSavedFundingFactorPerSecond", "type": "int256"}, {"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "fundingFeeAmountPerSizeDelta", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "claimableFundingAmountPerSizeDelta", "type": "tuple"}], "internalType": "struct MarketUtils.GetNextFundingAmountPerSizeResult", "name": "nextFunding", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "virtualPoolAmountForLongToken", "type": "uint256"}, {"internalType": "uint256", "name": "virtualPoolAmountForShortToken", "type": "uint256"}, {"internalType": "int256", "name": "virtualInventoryForPositions", "type": "int256"}], "internalType": "struct ReaderUtils.VirtualInventory", "name": "virtualInventory", "type": "tuple"}, {"internalType": "bool", "name": "isDisabled", "type": "bool"}], "internalType": "struct ReaderUtils.MarketInfo", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices[]", "name": "marketPricesList", "type": "tuple[]"}, {"internalType": "uint256", "name": "start", "type": "uint256"}, {"internalType": "uint256", "name": "end", "type": "uint256"}], "name": "getMarketInfoList", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"internalType": "uint256", "name": "borrowingFactorPerSecondForLongs", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFactorPerSecondForShorts", "type": "uint256"}, {"components": [{"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "fundingFeeAmountPerSize", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "claimableFundingAmountPerSize", "type": "tuple"}], "internalType": "struct ReaderUtils.BaseFundingValues", "name": "baseFunding", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "longsPayShorts", "type": "bool"}, {"internalType": "uint256", "name": "fundingFactorPerSecond", "type": "uint256"}, {"internalType": "int256", "name": "nextSavedFundingFactorPerSecond", "type": "int256"}, {"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "fundingFeeAmountPerSizeDelta", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "long", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "longToken", "type": "uint256"}, {"internalType": "uint256", "name": "shortToken", "type": "uint256"}], "internalType": "struct MarketUtils.CollateralType", "name": "short", "type": "tuple"}], "internalType": "struct MarketUtils.PositionType", "name": "claimableFundingAmountPerSizeDelta", "type": "tuple"}], "internalType": "struct MarketUtils.GetNextFundingAmountPerSizeResult", "name": "nextFunding", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "virtualPoolAmountForLongToken", "type": "uint256"}, {"internalType": "uint256", "name": "virtualPoolAmountForShortToken", "type": "uint256"}, {"internalType": "int256", "name": "virtualInventoryForPositions", "type": "int256"}], "internalType": "struct ReaderUtils.VirtualInventory", "name": "virtualInventory", "type": "tuple"}, {"internalType": "bool", "name": "isDisabled", "type": "bool"}], "internalType": "struct ReaderUtils.MarketInfo[]", "name": "", "type": "tuple[]"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}, {"internalType": "bytes32", "name": "pnlFactorType", "type": "bytes32"}, {"internalType": "bool", "name": "maximize", "type": "bool"}], "name": "getMarketTokenPrice", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}, {"components": [{"internalType": "int256", "name": "poolValue", "type": "int256"}, {"internalType": "int256", "name": "longPnl", "type": "int256"}, {"internalType": "int256", "name": "shortPnl", "type": "int256"}, {"internalType": "int256", "name": "netPnl", "type": "int256"}, {"internalType": "uint256", "name": "longTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "longTokenUsd", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenUsd", "type": "uint256"}, {"internalType": "uint256", "name": "totalBorrowingFees", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeePoolFactor", "type": "uint256"}, {"internalType": "uint256", "name": "impactPoolAmount", "type": "uint256"}], "internalType": "struct MarketPoolValueInfo.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "uint256", "name": "start", "type": "uint256"}, {"internalType": "uint256", "name": "end", "type": "uint256"}], "name": "getMarkets", "outputs": [{"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props[]", "name": "", "type": "tuple[]"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"internalType": "bool", "name": "maximize", "type": "bool"}], "name": "getNetPnl", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"internalType": "bool", "name": "isLong", "type": "bool"}, {"internalType": "bool", "name": "maximize", "type": "bool"}], "name": "getOpenInterestWithPnl", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "bytes32", "name": "key", "type": "bytes32"}], "name": "getOrder", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "callbackContract", "type": "address"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "initialCollateralToken", "type": "address"}, {"internalType": "address[]", "name": "swapPath", "type": "address[]"}], "internalType": "struct Order.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "enum Order.OrderType", "name": "orderType", "type": "uint8"}, {"internalType": "enum Order.DecreasePositionSwapType", "name": "decreasePositionSwapType", "type": "uint8"}, {"internalType": "uint256", "name": "sizeDeltaUsd", "type": "uint256"}, {"internalType": "uint256", "name": "initialCollateralDeltaAmount", "type": "uint256"}, {"internalType": "uint256", "name": "triggerPrice", "type": "uint256"}, {"internalType": "uint256", "name": "acceptablePrice", "type": "uint256"}, {"internalType": "uint256", "name": "executionFee", "type": "uint256"}, {"internalType": "uint256", "name": "callbackGasLimit", "type": "uint256"}, {"internalType": "uint256", "name": "minOutputAmount", "type": "uint256"}, {"internalType": "uint256", "name": "updatedAtBlock", "type": "uint256"}], "internalType": "struct Order.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "isLong", "type": "bool"}, {"internalType": "bool", "name": "shouldUnwrapNativeToken", "type": "bool"}, {"internalType": "bool", "name": "isFrozen", "type": "bool"}], "internalType": "struct Order.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Order.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"internalType": "bool", "name": "isLong", "type": "bool"}, {"internalType": "bool", "name": "maximize", "type": "bool"}], "name": "getPnl", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "marketAddress", "type": "address"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "bool", "name": "isLong", "type": "bool"}, {"internalType": "bool", "name": "maximize", "type": "bool"}], "name": "getPnlToPoolFactor", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "bytes32", "name": "key", "type": "bytes32"}], "name": "getPosition", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "collateralToken", "type": "address"}], "internalType": "struct Position.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "sizeInUsd", "type": "uint256"}, {"internalType": "uint256", "name": "sizeInTokens", "type": "uint256"}, {"internalType": "uint256", "name": "collateralAmount", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFactor", "type": "uint256"}, {"internalType": "uint256", "name": "fundingFeeAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "longTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "increasedAtBlock", "type": "uint256"}, {"internalType": "uint256", "name": "decreasedAtBlock", "type": "uint256"}], "internalType": "struct Position.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "isLong", "type": "bool"}], "internalType": "struct Position.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Position.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "contract IReferralStorage", "name": "referralStorage", "type": "address"}, {"internalType": "bytes32", "name": "positionKey", "type": "bytes32"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "uint256", "name": "sizeDeltaUsd", "type": "uint256"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "bool", "name": "usePositionSizeAsSizeDeltaUsd", "type": "bool"}], "name": "getPositionInfo", "outputs": [{"components": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address", "name": "collateralToken", "type": "address"}], "internalType": "struct Position.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "sizeInUsd", "type": "uint256"}, {"internalType": "uint256", "name": "sizeInTokens", "type": "uint256"}, {"internalType": "uint256", "name": "collateralAmount", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFactor", "type": "uint256"}, {"internalType": "uint256", "name": "fundingFeeAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "longTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "shortTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "increasedAtBlock", "type": "uint256"}, {"internalType": "uint256", "name": "decreasedAtBlock", "type": "uint256"}], "internalType": "struct Position.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "isLong", "type": "bool"}], "internalType": "struct Position.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Position.Props", "name": "position", "type": "tuple"}, {"components": [{"components": [{"internalType": "bytes32", "name": "referralCode", "type": "bytes32"}, {"internalType": "address", "name": "affiliate", "type": "address"}, {"internalType": "address", "name": "trader", "type": "address"}, {"internalType": "uint256", "name": "totalRebateFactor", "type": "uint256"}, {"internalType": "uint256", "name": "traderDiscountFactor", "type": "uint256"}, {"internalType": "uint256", "name": "totalRebateAmount", "type": "uint256"}, {"internalType": "uint256", "name": "traderDiscountAmount", "type": "uint256"}, {"internalType": "uint256", "name": "affiliateRewardAmount", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionReferralFees", "name": "referral", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "fundingFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "claimableLongTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "claimableShortTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "latestFundingFeeAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "latestLongTokenClaimableFundingAmountPerSize", "type": "uint256"}, {"internalType": "uint256", "name": "latestShortTokenClaimableFundingAmountPerSize", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionFundingFees", "name": "funding", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "borrowingFeeUsd", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "borrowingFeeAmountForFeeReceiver", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionBorrowingFees", "name": "borrowing", "type": "tuple"}, {"components": [{"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "uint256", "name": "uiFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "uiFeeAmount", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionUiFees", "name": "ui", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "collateralTokenPrice", "type": "tuple"}, {"internalType": "uint256", "name": "positionFeeFactor", "type": "uint256"}, {"internalType": "uint256", "name": "protocolFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "positionFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "feeReceiverAmount", "type": "uint256"}, {"internalType": "uint256", "name": "feeAmountForPool", "type": "uint256"}, {"internalType": "uint256", "name": "positionFeeAmountForPool", "type": "uint256"}, {"internalType": "uint256", "name": "positionFeeAmount", "type": "uint256"}, {"internalType": "uint256", "name": "totalCostAmountExcludingFunding", "type": "uint256"}, {"internalType": "uint256", "name": "totalCostAmount", "type": "uint256"}], "internalType": "struct PositionPricingUtils.PositionFees", "name": "fees", "type": "tuple"}, {"components": [{"internalType": "int256", "name": "priceImpactUsd", "type": "int256"}, {"internalType": "uint256", "name": "priceImpactDiffUsd", "type": "uint256"}, {"internalType": "uint256", "name": "executionPrice", "type": "uint256"}], "internalType": "struct ReaderPricingUtils.ExecutionPriceResult", "name": "executionPriceResult", "type": "tuple"}, {"internalType": "int256", "name": "basePnlUsd", "type": "int256"}, {"internalType": "int256", "name": "uncappedBasePnlUsd", "type": "int256"}, {"internalType": "int256", "name": "pnlAfterPriceImpactUsd", "type": "int256"}], "internalType": "struct ReaderUtils.PositionInfo", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "bytes32", "name": "positionKey", "type": "bytes32"}, {"internalType": "uint256", "name": "sizeDeltaUsd", "type": "uint256"}], "name": "getPositionPnlUsd", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}, {"internalType": "int256", "name": "", "type": "int256"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}], "name": "getSwapAmountOut", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "int256", "name": "", "type": "int256"}, {"components": [{"internalType": "uint256", "name": "feeReceiverAmount", "type": "uint256"}, {"internalType": "uint256", "name": "feeAmountForPool", "type": "uint256"}, {"internalType": "uint256", "name": "amountAfterFees", "type": "uint256"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "uint256", "name": "uiFeeReceiverFactor", "type": "uint256"}, {"internalType": "uint256", "name": "uiFeeAmount", "type": "uint256"}], "internalType": "struct SwapPricingUtils.SwapFees", "name": "fees", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "address", "name": "marketKey", "type": "address"}, {"internalType": "address", "name": "tokenIn", "type": "address"}, {"internalType": "address", "name": "tokenOut", "type": "address"}, {"internalType": "uint256", "name": "amountIn", "type": "uint256"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "tokenInPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "tokenOutPrice", "type": "tuple"}], "name": "getSwapPriceImpact", "outputs": [{"internalType": "int256", "name": "", "type": "int256"}, {"internalType": "int256", "name": "", "type": "int256"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"internalType": "bytes32", "name": "key", "type": "bytes32"}], "name": "getWithdrawal", "outputs": [{"components": [{"components": [{"internalType": "address", "name": "account", "type": "address"}, {"internalType": "address", "name": "receiver", "type": "address"}, {"internalType": "address", "name": "callbackContract", "type": "address"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}, {"internalType": "address", "name": "market", "type": "address"}, {"internalType": "address[]", "name": "longTokenSwapPath", "type": "address[]"}, {"internalType": "address[]", "name": "shortTokenSwapPath", "type": "address[]"}], "internalType": "struct Withdrawal.Addresses", "name": "addresses", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "marketTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "minLongTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "minShortTokenAmount", "type": "uint256"}, {"internalType": "uint256", "name": "updatedAtBlock", "type": "uint256"}, {"internalType": "uint256", "name": "executionFee", "type": "uint256"}, {"internalType": "uint256", "name": "callbackGasLimit", "type": "uint256"}], "internalType": "struct Withdrawal.Numbers", "name": "numbers", "type": "tuple"}, {"components": [{"internalType": "bool", "name": "shouldUnwrapNativeToken", "type": "bool"}], "internalType": "struct Withdrawal.Flags", "name": "flags", "type": "tuple"}], "internalType": "struct Withdrawal.Props", "name": "", "type": "tuple"}], "stateMutability": "view", "type": "function"}, {"inputs": [{"internalType": "contract DataStore", "name": "dataStore", "type": "address"}, {"components": [{"internalType": "address", "name": "marketToken", "type": "address"}, {"internalType": "address", "name": "indexToken", "type": "address"}, {"internalType": "address", "name": "longToken", "type": "address"}, {"internalType": "address", "name": "shortToken", "type": "address"}], "internalType": "struct Market.Props", "name": "market", "type": "tuple"}, {"components": [{"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "indexTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "longTokenPrice", "type": "tuple"}, {"components": [{"internalType": "uint256", "name": "min", "type": "uint256"}, {"internalType": "uint256", "name": "max", "type": "uint256"}], "internalType": "struct Price.Props", "name": "shortTokenPrice", "type": "tuple"}], "internalType": "struct MarketUtils.MarketPrices", "name": "prices", "type": "tuple"}, {"internalType": "uint256", "name": "marketTokenAmount", "type": "uint256"}, {"internalType": "address", "name": "uiFeeReceiver", "type": "address"}], "name": "getWithdrawalAmountOut", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}, {"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}]')





class Collector:
    def __init__(self):
        self.content = []
        self.built_in_print = print  # Save the original print function

    def start_collecting(self):
        global print
        print = self.collect_prints

    def collect_prints(self, *args, **kwargs):
        output = " ".join(map(str, args))  # Convert all arguments to strings
        self.content.append(output)
        self.built_in_print(*args, **kwargs)  # Print to standard output

    def stop_collecting(self):
        global print
        print = self.built_in_print  # Restore the original print function




# Google sheet number dictionary
dex_to_open_positions_dictionary = {
    "GMXV1" : 1, # Index 3 corresponds to the fourth sheet
    "GMXV2" : 2,
    "GAINS" : 3, 
    "MUX" : 4,
}




## (READY) (August 4th 2024) (this buys atleast min_qty) (with email top button) (try adn except in sheets and emailing)
## ----------------------Complete Trading Bot Class for all trading related things--------------------------
class Trading_Things: 
    
    def __init__(self):
        try:
            # Specify the path to your service account JSON file
            # credentials_file = "btc-server-trading-data-77c9789d4ab9.json"
            # https://www.youtube.com/watch?v=zCEJurLGFRk&t=1318s   Refer to this video in future if needed for google sheet api operations in gspread operations
           

            # Initiating googlesheets service client
            self.scopes = ["https://www.googleapis.com/auth/spreadsheets"]
            # Load credentials from the service account file
            self.creds = Credentials.from_service_account_info(credentials_file, scopes=self.scopes)
            # Authorize the client using the loaded credentials
            self.g_client = gspread.authorize(self.creds)
            # Open the workbook by its ID
            self.g_workbook = self.g_client.open_by_key(sheet_id)

            # Access the worksheet, worksheet at index 0 corresponds to the first sheet
            self.trading_worksheet = self.g_workbook.get_worksheet(0)
            # Check if the first row is empty
            if not self.trading_worksheet.row_values(1):
                # Define the column names
                column_names = [
                    'time',
                    'trade_order_id',
                    'address',
                    'symbol',
                    'is_long_short',
                    'trade_type',
                    'leads_price',
                    'price',
                    'weighted_score_ratio',
                    'leads_max_volume',
                    'leads_leverage',
                    'leads_transaction_quantity',
                    'leads_transaction_amount',
                    'our_leverage',
                    'our_transaction_quantity',
                    'our_transaction_amount',
                    'leads_total_hold',
                    'leads_total_investment',
                    'avg_leads_coin_price',
                    'our_total_hold',
                    'our_total_investment',
                    'avg_coin_price',
                    'total_hold_ratio',
                    'stop_loss_price',
                    'stop_loss_order_id',
                    'is_stop_loss_executed',
                    'is_liquidated',
                    'take_profit_price',
                    'take_profit_order_id',
                    'PNL',
                    'DEX',
                    'available_balance'
                ]

                # Insert column names into the first row
                self.trading_worksheet.append_row(column_names)

        except Exception as e:
            content = f"Error \"{e}\" happened while uploading open positions to google sheets.\nException: {traceback.format_exc()}"
            print(content)
            self.send_message("ALERT", content)



#---Others----------
    def get_current_time(self):
        india_timezone = pytz.timezone("Asia/Kolkata")
        current_time = datetime.now(india_timezone).strftime("%H:%M:%S %d %B %Y")
        return current_time

    # Function to generate HTML with the date and Google Sheet link
    def generate_html_with_date(self):
        # Get the current date
        current_time = self.get_current_time()
        current_date = ' '.join(current_time.split(' ')[1:4])  # Extracting date part
        
        html_content = f"""
        <html>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background: transparent;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background: transparent; padding: 0 10px;">
            <tr>
                <td style="text-align: center;">
                <a href="{google_sheet_url}" style="
                    display: inline-block; width: 100%; max-width: 600px; /* Full width but not exceeding 600px */
                    padding: 10px 20px; /* Increased padding for taller button */
                    font-size: 16px; font-weight: bold; color: #fff; background-color: #007bff; 
                    text-decoration: none; border: none; /* Remove border */
                    border-radius: 4px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                    transition: background-color 0.3s ease;
                    text-align: center; /* Center text in the button */
                    height: auto; /* Allow button height to adjust automatically */
                    line-height: 1.2; /* Adjust line-height to better fit the increased height */
                    box-sizing: border-box; /* Include padding and border in element's width and height */
                    margin-bottom: 20px; /* Space below the button */
                "> 
                    Google Sheet Live
                </a>
                </td>
            </tr>
            <tr>
                <td style="height: 20px;"></td> <!-- Blank line for additional space -->
            </tr>
            </table>
        </body>
        </html>
        """
        return html_content

    # Gmail services
    def gmail_alerts_binance(self, new_row):

        try:
            message_trade =  f"{new_row['is_long_short'][0]} : {new_row['trade_type'][0]} : {new_row['symbol'][0]} : {new_row['DEX'][0]} at {new_row['time'][0]}"
            message = MIMEMultipart()  
            message["From"] = sender_email
            message["To"] = ", ".join(receiver_email)
            message["Subject"] = message_trade
    
            # Extract data from new_row dictionary
            time = new_row['time'][0]
            trade_order_id = new_row['trade_order_id'][0]
            address = new_row['address'][0]
            symbol = new_row['symbol'][0]
            is_long_short = new_row['is_long_short'][0]
            trade_type = new_row['trade_type'][0]
            leads_price = new_row['leads_price'][0]  
            price = new_row['price'][0]
            weighted_score_ratio = new_row['weighted_score_ratio'][0]
            leads_max_volume = new_row['leads_max_volume'][0]
            leads_leverage = new_row['leads_leverage'][0]
            leads_transaction_quantity = new_row['leads_transaction_quantity'][0]
            leads_transaction_amount = new_row['leads_transaction_amount'][0]
            our_leverage = new_row['our_leverage'][0]
            our_transaction_quantity = new_row['our_transaction_quantity'][0]
            our_transaction_amount = new_row['our_transaction_amount'][0]
            leads_total_hold = new_row['leads_total_hold'][0]
            leads_total_investment = new_row['leads_total_investment'][0] 
            avg_leads_coin_price = new_row['avg_leads_coin_price'][0]
            our_total_hold = new_row['our_total_hold'][0]
            our_total_investment = new_row['our_total_investment'][0] 
            avg_coin_price = new_row['avg_coin_price'][0]
            total_hold_ratio = new_row['total_hold_ratio'][0]
            stop_loss_price = new_row['stop_loss_price'][0]
            stop_loss_order_id = new_row['stop_loss_order_id'][0]
            is_stop_loss_executed = new_row['is_stop_loss_executed'][0]
            is_liquidated = new_row['is_liquidated'][0]
            take_profit_price = new_row['take_profit_price'][0]
            take_profit_order_id = new_row['take_profit_order_id'][0]
            PNL = new_row['PNL'][0]
            DEX = new_row['DEX'][0]
            available_balance = new_row['available_balance'][0]

            # Format data into rows for the table
            rows = [
                ["Time", str(time)],
                ["Trade Order ID", str(trade_order_id)],
                ["Leads Address", str(address)],
                ["Symbol", str(symbol)],
                ["Long/Short", str(is_long_short)],
                ["Trade Type", str(trade_type)],  # Updated to match `new_row`
                ["Leads Price", str(leads_price) + " USDT"],  # Added column
                ["Price", str(price) + " USDT"],
                ["Weighted Score Ratio", str(weighted_score_ratio)],  # Added column
                ["Leads Max Volume", str(leads_max_volume) + " USDT"],  # Added column
                ["Leads Leverage", str(leads_leverage)],
                ["Leads Transaction Quantity", str(leads_transaction_quantity) + ' ' + str(symbol)],
                ["Leads Transaction Amount", str(leads_transaction_amount) + " USDT"],
                ["Our Leverage", str(our_leverage)],
                ["Our Transaction Quantity", str(our_transaction_quantity) + ' ' + str(symbol)],
                ["Our Transaction Amount", str(our_transaction_amount) + " USDT"],
                ["Leads Total Hold", str(leads_total_hold) + ' ' + str(symbol)],
                ["Leads Total Investment", str(leads_total_investment) + " USDT"],  # Added column
                ["Average Leads Coin Price", str(avg_leads_coin_price) + " USDT"],  # Added column
                ["Our Total Hold", str(our_total_hold) + ' ' + str(symbol)],
                ["Our Total Investment", str(our_total_investment) + " USDT"],  # Added column
                ["Average Coin Price", str(avg_coin_price) + " USDT"],
                ["Total Hold Ratio", str(total_hold_ratio)],
                ["Stop Loss Price", str(stop_loss_price) + " USDT"],
                ["Stop Loss Order ID", str(stop_loss_order_id)],
                ["Is Stop Loss Executed", str(is_stop_loss_executed)],
                ["Is Liquidated", str(is_liquidated)],
                ["Take Profit Price", str(take_profit_price) + " USDT"],
                ["Take Profit Order ID", str(take_profit_order_id)],
                ["PNL", str(PNL) + " USDT"],
                ["DEX", str(DEX)],  # Updated to match `new_row`
                ["available_balance", str(available_balance)],
            ]


            # Create the table
            table_html = self.create_table_html(rows)

            message.attach(MIMEText(self.generate_html_with_date(), "html"))

            # Attach table as HTML to the email
            message.attach(MIMEText(table_html, "html"))

            email_server = smtplib.SMTP("smtp.gmail.com", 587)
            email_server.starttls()
            email_server.login(sender_email, email_password)
            email_server.sendmail(sender_email, receiver_email, message.as_string())

        except Exception as e:
            print(f"Error occurred while constructing or sending the email.\nException: {traceback.format_exc()}")

    # Function to create a table as HTML from rows
    def create_table_html(self, rows):
        """Create a striped table as HTML."""
        table_html = "<table style='width: 70%; border-collapse: collapse;'>"
        for i, row in enumerate(rows):
            if i % 2 == 0:
                table_html += "<tr style='background-color: #f2f2f2;'>"
            else:
                table_html += "<tr style='background-color: #ffffff;'>"
            table_html += f"<td style='width: 50%; padding: 8px; color: black; font-weight: bold;'>{row[0]}</td>"
            table_html += "<td style='padding: 8px; color: black;'>:</td>"
            table_html += f"<td style='width: 50%; padding: 8px; color: black;'>{row[1]}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        return table_html

    # Emailer
    def send_message(self, message_type, content):

        email_server = smtplib.SMTP("smtp.gmail.com", 587)
        email_server.starttls()
        email_server.login(sender_email, email_password)

        if message_type == "ALERT":
            try:
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = ", ".join(receiver_email)
                message["Subject"] = f"ALERT {DEX}: Attention required in binance server at {self.get_current_time()}"
                message.attach(MIMEText(self.generate_html_with_date(), "html"))
                body = (f"{content}")
                message.attach(MIMEText(body, "plain"))         

                email_server.sendmail(sender_email, receiver_email, message.as_string())
            except Exception as e:
                print(f"Error occurred while sending the ALERT message.\nException: {traceback.format_exc()}")

                
        elif message_type == "UPDATE":
            try:
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = ", ".join(receiver_email)
                message["Subject"] = "24 HRS SUMMARY: Liquidated trade got closed."
                message.attach(MIMEText(self.generate_html_with_date(), "html"))
                body = (f"{content}")
                message.attach(MIMEText(body, "plain"))         

                email_server.sendmail(sender_email, receiver_email, message.as_string())

            except Exception as e:
                print(f"Error occurred while sending the UPDATE message.\nException: {traceback.format_exc()}")
                
        elif message_type == "CRASHED":
            try:
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = ", ".join(receiver_email)
                message["Subject"] = f"CRASHED {DEX}: Program stopped due to outside error at {self.get_current_time()}"
                message.attach(MIMEText(self.generate_html_with_date(), "html"))
                body = (f"{content}")
                message.attach(MIMEText(body, "plain"))         

                email_server.sendmail(sender_email, receiver_email, message.as_string())
            except Exception as e:
                print(f"Error occurred while sending the CRASHED message.\nException: {traceback.format_exc()}")
                
        else:
            print("Invalid message type, try sending 'ALERT', 'UPDATE' or 'CRASHED'")



#---Sheets and DF Management----------
    def clear_google_sheet(self, sheet_number, password):
        
        for sheet in sheet_number:      
            if (sheet in [0, 1, 2, 3, 4, 5, 6]) & (password == "yesdeleteit"):

                # Access the worksheet, worksheet at index 0 corresponds to the first sheet
                worksheet = self.g_workbook.get_worksheet(sheet)
                
                # Clear the contents of the worksheet
                worksheet.clear()
                
                print(f"Cleared Successfully sheet {sheet}")
                
            else:
                print("Wrong Sheet Number or Password, Kindly try : 0, 1 or 2")

    # Function to insert trading data to google sheet
    def insert_row_to_google_sheet_traders(self, data):
        try:
            # Define the values to be inserted as a new row
            values = [
                data['time'][0],
                data['trade_order_id'][0],
                data['address'][0],
                data['symbol'][0],
                data['is_long_short'][0],
                data['trade_type'][0],
                data['leads_price'][0],
                data['price'][0],
                data['weighted_score_ratio'][0],
                data['leads_max_volume'][0],
                data['leads_leverage'][0],
                data['leads_transaction_quantity'][0],
                data['leads_transaction_amount'][0],
                data['our_leverage'][0],
                data['our_transaction_quantity'][0],
                data['our_transaction_amount'][0],
                data['leads_total_hold'][0],
                data['leads_total_investment'][0],
                data['avg_leads_coin_price'][0],
                data['our_total_hold'][0],
                data['our_total_investment'][0],
                data['avg_coin_price'][0],
                data['total_hold_ratio'][0],
                data['stop_loss_price'][0],
                data['stop_loss_order_id'][0],
                data['is_stop_loss_executed'][0],
                data['is_liquidated'][0],
                data['take_profit_price'][0],
                data['take_profit_order_id'][0],
                data['PNL'][0],
                data['DEX'][0],
                data['available_balance'][0]
            ]

            # Convert all int64 or float64 values to JSON-serializable Python native types... MODIFIED
            values = [int(item) if isinstance(item, np.int64) else float(item) if isinstance(item, np.float64) else item for item in values]

            # Append the row to the worksheet
            self.trading_worksheet.append_row(values)

            print("Row inserted successfully into G-Sheet:TRADING.")

        except Exception as e:
            content = f"Error \"{e}\" happened while appending new trade to google sheets.\nException: {traceback.format_exc()}"
            print(content)
            self.send_message("ALERT", content)

    # trading_data_df is defined globally
    def add_to_trading_data_df(self, time, trade_order_id, address, symbol, is_long_short, trade_type, leads_price, price, weighted_score_ratio, leads_max_volume, leads_leverage, leads_transaction_quantity,
                        leads_transaction_amount, our_leverage, our_transaction_quantity, our_transaction_amount, leads_total_hold, leads_total_investment, avg_leads_coin_price,
                        our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_price, stop_loss_order_id,
                        is_stop_loss_executed,is_liquidated, take_profit_price, take_profit_order_id, PNL):

        global trading_data_df 

        def side_convention(is_long_short, trade_type):
            if is_long_short == "LONG":
                if trade_type == "BUY":
                    return "OPEN"
                elif trade_type == "SELL": ### it shoudl be SELL
                    return "CLOSE"
                elif trade_type == "BANNED":
                    return "BANNED"
                elif trade_type == "LIQUIDATED":
                    return "LIQUIDATED"
                else:
                    return None
            elif is_long_short == "SHORT":
                if trade_type == "BUY":
                    return "CLOSE"
                elif trade_type == "SELL":
                    return "OPEN"
                elif trade_type == "BANNED":
                    return "BANNED"
                elif trade_type == "LIQUIDATED":
                    return "LIQUIDATED"
                else:
                    return None
            else:
                return None  # Handle invalid input

        new_row = {
            'time': [time],
            'trade_order_id': [trade_order_id],
            'address': [address],
            'symbol': [symbol],
            'is_long_short': [is_long_short],
            'trade_type': [side_convention(is_long_short, trade_type)],
            'leads_price': [leads_price],
            'price': [price],
            'weighted_score_ratio': [weighted_score_ratio],
            'leads_max_volume': [leads_max_volume],
            'leads_leverage': [leads_leverage],
            'leads_transaction_quantity': [leads_transaction_quantity],
            'leads_transaction_amount': [leads_transaction_amount],
            'our_leverage': [our_leverage],
            'our_transaction_quantity': [our_transaction_quantity],
            'our_transaction_amount': [our_transaction_amount],
            'leads_total_hold': [leads_total_hold],
            'leads_total_investment': [leads_total_investment],
            'avg_leads_coin_price': [avg_leads_coin_price],
            'our_total_hold': [our_total_hold],
            'our_total_investment': [our_total_investment],
            'avg_coin_price': [avg_coin_price],
            'total_hold_ratio': [total_hold_ratio],
            'stop_loss_price': [stop_loss_price],
            'stop_loss_order_id': [stop_loss_order_id],
            'is_stop_loss_executed': [is_stop_loss_executed],
            'is_liquidated': [is_liquidated],
            'take_profit_price': [take_profit_price],
            'take_profit_order_id': [take_profit_order_id],
            'PNL': [PNL],
            'DEX': dex_name,
            'available_balance': [self.return_available_balance()],
        }
        
        # To insert trading data to google sheet
        self.insert_row_to_google_sheet_traders(new_row)
        
        self.gmail_alerts_binance(new_row)
        
        new_row_df = pd.DataFrame(new_row)

        trading_data_df = pd.concat([trading_data_df, new_row_df], ignore_index=True)

        # Extract the header and the row from the dictionary
        header = new_row_df.keys()
        row = [value[0] for value in new_row.values()]

        # Check if the file exists
        file_exists = os.path.isfile(trading_data_df_path)

        # Open the file in append mode
        with open(trading_data_df_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            # If the file does not exist, write the header
            if not file_exists:
                writer.writerow(header)
            # Write the new row
            writer.writerow(row)

        print(f"New row added to {trading_data_df_path}")
        

    def get_and_upload_open_positions_to_sheets(self):
        try:
            # Access the specific worksheet
            self.positions_worksheet = self.g_workbook.get_worksheet(dex_to_open_positions_dictionary[DEX[0]]) # Index 0 corresponds to the 1st sheet

            # Define the column names
            column_names = [
                'time',
                'trade_order_id',
                'address',
                'symbol',
                'is_long_short',
                'last_trade_type',
                'leads_total_hold',
                'leads_total_investment',
                'leads_leverage',
                'avg_leads_coin_price',
                'our_total_hold',
                'our_total_investment',
                'our_leverage',
                'avg_coin_price',
                'total_hold_ratio',
                'stop_loss_price',
                'stop_loss_order_id',
                'take_profit_price',
                'take_profit_order_id',
                'DEX'
            ]
            
            # Prepare the list of values to write
            values = [column_names]  # Add column names as the first row

            # Group by address, symbol, and is_long_short
            grouped_df = trading_data_df.groupby(['address', 'symbol', 'is_long_short'])

            # Iterate over each group
            for name, group in grouped_df:
                # Pass data to the check_old_stop_loss function (address, symbol, position)
                trader_position_df = self.get_position_of_trader_from_trading_data_df(trading_data_df, name[0], name[1], name[2])
                
                if not trader_position_df.empty:
                    data = trader_position_df.iloc[-1]

                    if data['our_total_hold'] != 0:
                        row = [
                            str(data['time']),
                            data['trade_order_id'],
                            data['address'],
                            data['symbol'],
                            data['is_long_short'],
                            data['trade_type'],
                            data['leads_total_hold'],
                            data['leads_total_investment'],
                            data['leads_leverage'],
                            data['avg_leads_coin_price'],
                            data['our_total_hold'],
                            data['our_total_investment'],
                            data['our_leverage'],
                            data['avg_coin_price'],
                            data['total_hold_ratio'],
                            data['stop_loss_price'],
                            data['stop_loss_order_id'],
                            data['take_profit_price'],
                            data['take_profit_order_id'],
                            data['DEX']
                        ]
                        values.append(row)  # Add each row of data

            # Clear all rows
            self.positions_worksheet.clear()  # This clears all content in the sheet

            # Write new data starting from cell A1
            self.positions_worksheet.update('A1', values)

        except Exception as e:
            content = f"Error \"{e}\" happened while uploading open positions to google sheets.\nException: {traceback.format_exc()}"
            print(content)
            self.send_message("ALERT", content)

    def get_summary_and_send_email(self):

        try:
            global last_email_sent_date

            message_trade =  f"{dex_name}: SUMMARY 24 HRS ({summary_sending_hour}:00 yesterday - {summary_sending_hour}:00 today)"
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = ", ".join(receiver_email)
            message["Subject"] = message_trade

            # Convert the 'time' column to datetime format
            trading_data_df['time'] = pd.to_datetime(trading_data_df['time'], format="%H:%M:%S %d %B %Y")

            # Get the current time in IST
            now = self.get_current_time()

            # Convert the 'now' time string to a datetime object
            now = datetime.strptime(now, "%H:%M:%S %d %B %Y")

            # Calculate the start time (summary_sending_hour PM of the previous day)
            previous_day = (now - timedelta(days=1)).replace(hour=summary_sending_hour, minute=0, second=0, microsecond=0)

            # Calculate the end time (summary_sending_hour PM today)
            today = now.replace(hour=summary_sending_hour, minute=0, second=0, microsecond=0)

            # Filter rows from summary_sending_hour PM of the previous day to summary_sending_hour PM today
            last_24_hours = trading_data_df[(trading_data_df['time'] >= previous_day) & (trading_data_df['time'] <= today)]

            # Group by 'address', 'symbol', 'is_long_short' and count the number of unique groups
            unique_group_count = last_24_hours.groupby(['address', 'symbol', 'is_long_short']).ngroups

            # Count the number of rows within the last 24 hours
            row_count = len(last_24_hours)

            # Sum the PNL column within the last 24 hours
            pnl_sum = last_24_hours['PNL'].sum()

            # Count occurrences in 'tradetype' column
            close_count = last_24_hours['trade_type'].value_counts().get('CLOSE', 0)
            open_count = last_24_hours['trade_type'].value_counts().get('OPEN', 0)
            liquidated_count = last_24_hours['trade_type'].value_counts().get('LIQUIDATED', 0)
            banned_count = last_24_hours['trade_type'].value_counts().get('BANNED', 0)

            rows = [
                    ["Time", self.get_current_time()],
                    ["Total POSITIONS", unique_group_count],
                    ["Total Trades", row_count],
                    ["Total OPEN Trades", open_count],
                    ["Total CLOSE Trades", close_count],
                    ["Total LIQUIDATED Trades", liquidated_count],
                    ["Total BANNED Trades", banned_count],
                    ["Total PNL", pnl_sum],
                    ["DEX", dex_name],]

            table_html = self.create_table_html(rows)

            # Attach table as HTML to the email
            message.attach(MIMEText(table_html, "html"))

            # Add the link below the table
            link_text = "\n\nCheck Google Sheet for live server trading updates here:"
            link_url = google_sheet_url
            link_html = f"<p><a href='{link_url}'>{link_text}</a></p>"
            message.attach(MIMEText(link_html, "html"))

            email_server = smtplib.SMTP("smtp.gmail.com", 587)
            email_server.starttls()
            email_server.login(sender_email, email_password)
            email_server.sendmail(sender_email, receiver_email, message.as_string())

            last_email_sent_date = now.date()  # Update the date of the last email sent

        except Exception as e:
            print(f"Error occurred while constructing or sending the email. \nException: {traceback.format_exc()}")



    #---Others----------
    # Get the whole position data
    def get_position_of_trader_from_trading_data_df(self, trading_data_df, address_to_search, symbol_to_search, is_long_short_to_search):
        trader_position_df = trading_data_df[
            (trading_data_df['address'] == address_to_search) &
            (trading_data_df['symbol'] == symbol_to_search) &
            (trading_data_df['is_long_short'] == is_long_short_to_search)
        ]
        return trader_position_df

    # Get last row data of the position
    def get_last_row_of_trader_in_trading_data_df(self, trading_data_df, address_to_search, symbol_to_search, is_long_short_to_search):

        trader_position_df = self.get_position_of_trader_from_trading_data_df(trading_data_df, address_to_search, symbol_to_search, is_long_short_to_search)
        
        if not trader_position_df.empty:
            last_row_trader_personal_df = trader_position_df.iloc[-1]
            
            #print("Last row present.")

            if last_row_trader_personal_df['our_total_hold'] == 0 or last_row_trader_personal_df['trade_type'] == 'BANNED':
                was_last_row_present = True
                return 0, 0, 0, 0, 0, 0, 0, 0, None, 0, was_last_row_present
            else:
                leads_total_hold = float(last_row_trader_personal_df['leads_total_hold'])
                leads_total_investment = float(last_row_trader_personal_df['leads_total_investment'])
                avg_leads_coin_price = float(last_row_trader_personal_df['avg_leads_coin_price'])
                leads_leverage = float(last_row_trader_personal_df['leads_leverage'])

                our_total_hold = float(last_row_trader_personal_df['our_total_hold'])
                our_total_investment = float(last_row_trader_personal_df['our_total_investment'])
                avg_coin_price = float(last_row_trader_personal_df['avg_coin_price'])

                total_hold_ratio = float(last_row_trader_personal_df['total_hold_ratio'])
                stop_loss_order_id = last_row_trader_personal_df['stop_loss_order_id']
                stop_loss_price = float(last_row_trader_personal_df['stop_loss_price'])

                was_last_row_present = True

                return leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present
            
        else:
            was_last_row_present = False
            return 0, 0, 0, 0, 0, 0, 0, 0, None, 0, was_last_row_present
    
    #Fetching open_side value i.e buy or sell
    def sideAndCounterSideForBinance(self, position_side):
        open_side = "BUY" if position_side == "LONG" else "SELL"
        close_side = "SELL" if position_side == "LONG" else "BUY" # Used for SL and TP
        return open_side, close_side
    

    # Checking old stoploss status and inputing new row immedeately if stoploss of the position is executed
    def check_old_stop_loss(self, client, trading_data_df, address, symbol,  position_side):
        
        #Getting Data from leads last row in this position
        leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)

        #Inititalizing variables
        stop_PNL = 0
        PNL = 0

        try:
            if stop_loss_order_id is not None:
                market_order_status = client.futures_get_order(symbol=symbol, orderId=stop_loss_order_id)
                if market_order_status['status'] == 'FILLED':
                    print("\n\n")
                    weighted_score_ratio = traders_list['Ranking_Score'][traders_list['account'] == address].iloc[0] / traders_list['Ranking_Score'].sum()
                    leads_max_volume = traders_list['max_volume'][traders_list['account'] == address].iloc[0]

                    print(f"\n\nSTOP LOSS order filled for [address: {address}, symbol: {symbol}, position_side: {position_side}]")
                    new_leads_total_hold = 0
                    new_our_total_hold = 0
                    new_avg_coin_price = 0
                    new_total_hold_ratio= 0
                    #Fetching open_side value i.e buy or sell
                    open_side, close_side = self.sideAndCounterSideForBinance(position_side)
                    #Now using the details came from the filled order status
                    marketOrderQty, marketOrderPrice = float(market_order_status['executedQty']), float(market_order_status['avgPrice'])
                    new_our_transaction_amount = marketOrderQty * marketOrderPrice

                    # PNL Calculation
                    y = 1 if position_side == "LONG" else -1
                    stop_PNL = marketOrderQty * (marketOrderPrice - avg_coin_price) * (y)      

                    print(f"address: {address}\n"
                            f"symbol: {symbol}\n"
                            f"position_side: {position_side}\n"
                            f"transaction_quantity: {marketOrderQty}\n"
                            f"transaction_amount: {new_our_transaction_amount}\n"
                            f"stop_PNL: {stop_PNL}")
                    
                    # Append new row in the Trading_df with all updated details details.
                    self.add_to_trading_data_df(
                        time=self.get_current_time(), 
                        trade_order_id=stop_loss_order_id,
                        address=address, 
                        symbol=symbol, 
                        is_long_short=position_side,
                        trade_type=close_side,
                        leads_price=0,
                        price=marketOrderPrice,
                        weighted_score_ratio=weighted_score_ratio,
                        leads_max_volume=leads_max_volume,
                        leads_leverage=leads_leverage,
                        leads_transaction_quantity=0,
                        leads_transaction_amount=0,
                        our_leverage=our_leverage,
                        our_transaction_quantity=marketOrderQty,
                        our_transaction_amount=new_our_transaction_amount,
                        leads_total_hold=new_leads_total_hold, 
                        leads_total_investment=leads_total_investment,
                        avg_leads_coin_price=avg_leads_coin_price,
                        our_total_hold=0,
                        our_total_investment=our_total_investment,
                        avg_coin_price=new_avg_coin_price,
                        total_hold_ratio=new_total_hold_ratio,
                        stop_loss_price=0,
                        stop_loss_order_id=None,
                        is_stop_loss_executed=True,
                        is_liquidated=False,
                        take_profit_price=0,
                        take_profit_order_id=None,
                        PNL=stop_PNL
                    )
                    print("\n\n")

                    return True
                    
                elif market_order_status['status'] == 'EXPIRED':
                    print("\n\n")
                    Alert_note = f"Panic, old stoploss orderId status is 'EXPIRED' (Now banning the position for {ban_time_hours}hrs). stop_loss_order_id:{stop_loss_order_id} (Please close the position manually)"
                    #Witing content for email
                    print(Alert_note)
                    content = f"{Alert_note},\n\naddress: {address},\nsymbol:{symbol},\nis_long_short:{position_side},\nstop_loss_order_id:{stop_loss_order_id},\ntime: {self.get_current_time()},\nour_total_hold:{our_total_hold},\navg_coin_price:{avg_coin_price}\n"
                    self.send_message("ALERT", content)
                    self.add_to_ban_list(address, symbol, position_side, stop_loss_order_id, 0, 0, our_total_hold, avg_coin_price) # Added to "ban_positions_info_list"
                    print("\n\n")
                    return False
                
                elif market_order_status['status'] == 'CANCELED':
                    print("\n\n")
                    Alert_note = f"Panic, old stoploss orderId status is already 'CANCELED' (Now banning the position for {ban_time_hours}hrs). stop_loss_order_id:{stop_loss_order_id} (Please close the position manually)"
                    #Witing content for email
                    print(Alert_note)
                    content = f"{Alert_note},\n\naddress: {address},\nsymbol:{symbol},\nis_long_short:{position_side},\nstop_loss_order_id:{stop_loss_order_id},\ntime: {self.get_current_time()},\nour_total_hold:{our_total_hold},\navg_coin_price:{avg_coin_price}\n"
                    self.send_message("ALERT", content)
                    self.add_to_ban_list(address, symbol, position_side, stop_loss_order_id, 0, 0, our_total_hold, avg_coin_price) # Added to "ban_positions_info_list"
                    print("\n\n")
                    return False
                
                else:
                    # print("Old stop-loss order was not filled")
                    return True
                
            else:
                # print("Old stop-loss order was not present in df")
                return True

        except Exception as e:
            Alert_note = f"\n\nException happened while checking old stop_loss through check_old_stop_loss function.\n\naddress: {address}, symbol: {symbol}, position_side: {position_side}"
            print(Alert_note)
            content = f"{Alert_note},\nstop_loss_order_id:{stop_loss_order_id},\ntime: {self.get_current_time()},\nour_total_hold:{our_total_hold},\navg_coin_price:{avg_coin_price}\nException: {traceback.format_exc()}"
            self.send_message("ALERT", content)
            print("\n\n")
            return False

    # To check last stop loss order id status
    def check_last_stop_loss_order_id_status(self, client, trading_data_df):
        # Group by address, symbol, and is_long_short
        grouped_df = trading_data_df.groupby(['address', 'symbol', 'is_long_short'])
        # Iterate over each group
        for name, group in grouped_df:
            # Pass data to the check_old_stop_loss function
            self.check_old_stop_loss(client, trading_data_df, name[0], name[1], name[2])

    def return_available_balance(self):
        # Get account information
        try:
            account_info = client.futures_account()
            available_balance = round(float(account_info['availableBalance']), 2)
            available_balance = str(available_balance)
            return available_balance
        except Exception as e:
            print(f"Error occurred during available balance fetching from Binance for uploading to available_balance column in df.\nException: {traceback.format_exc()}")
            return None

    # Round up to ceiling
    def round_up_to_ceil_with_precision(self, min_qnt, precision):
        # Calculate the raw quantity
        raw_quantity = min_qnt
        # Calculate the factor for the given precision
        precision_factor = 10 ** precision
        # Apply ceiling to round up and then adjust for precision
        rounded_quantity = math.ceil(raw_quantity * precision_factor) / precision_factor
        return rounded_quantity

    # Round off to floor
    def floor_decimal(self, value, precision):
        # Convert the value to a Decimal
        decimal_value = Decimal(str(value))
        # Create a string for the desired precision (e.g., '1.00' for 2 decimal places)
        precision_str = '1.' + '0' * precision
        # Floor the decimal value to the specified precision
        floored_value = decimal_value.quantize(Decimal(precision_str), rounding=ROUND_FLOOR)
        return floored_value




#---Opening----------
    def ultimate_openTrade(self, client, traders_list, address, coin, position_side, asset_price, transaction_amount, transaction_quantity, new_leads_leverage):
        
        print("Time:", self.get_current_time())
        symbol = coin + "USDT"
        current_trade_orderId = None

        # Opening Trades
        def openTrade(client, traders_list, address, symbol, position_side, asset_price, transaction_amount, transaction_quantity, new_leads_leverage):
            
            PNL = 0
            stop_PNL = 0
            nonlocal current_trade_orderId
            # Fetching coin price from Binance
            #---------------------------
            try:
                exchange_information = client.futures_exchange_info()
                symbol_info = next((s for s in exchange_information['symbols'] if s['symbol'] == symbol), None)  # corrected line
                if symbol_info:
                    # Precision for the quantity
                    quantity_precision = next((f['stepSize'] for f in symbol_info['filters'] if f['filterType'] == 'MARKET_LOT_SIZE'), None)
                    # Precision for the price in dollar
                    price_precision =  next((f['tickSize'] for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
                    # Minimum notional value (minimum dollars)
                    min_notional = float(next((f['notional'] for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None))
                    # Get integer value of precision
                    quantity_precision_integer = 0 if '.' not in str(quantity_precision) else len(
                        str(quantity_precision).split('.')[1].rstrip('0')) if str(quantity_precision) else None
                    price_precision_integer = 0 if '.' not in str(price_precision) else len(
                        str(price_precision).split('.')[1].rstrip('0')) if str(price_precision) else None
                    quantity_precision_integer = int(quantity_precision_integer)
                    price_precision_integer = int(price_precision_integer)

                    #Printing lead's qunatity and amount
                    transaction_amount = float(self.floor_decimal(transaction_amount, price_precision_integer))
                    transaction_quantity = float(self.floor_decimal(transaction_quantity, quantity_precision_integer))
                    print(f"Lead's transaction amaount: ", transaction_amount)
                    print(f"Lead's transaction quantity: ", transaction_quantity)

                    if transaction_amount == 0 or transaction_quantity == 0:
                        print("Lead's Quantites are zero when rounded. Rejecting trade.")
                        return True, None
                    
                    print(f"min_notional: {min_notional}")
                    print(f"quantity_precision_integer: {quantity_precision_integer}")
                    print(f"price_precision_integer: {price_precision_integer}")
                    # Getting price on binance
                    try:
                        ticker = client.futures_symbol_ticker(symbol=symbol)
                        price_on_bin = float(ticker['price'])
                        print(f"Current market price of {symbol}: {price_on_bin}")
                    except Exception as e:
                        print(f"Error occurred during coin {symbol} price fetching from Binance.\nxception: {traceback.format_exc()}")
                        return 1001, f"Error occurred during coin {symbol} price fetching from Binance.\nException: {e}"
                                    
                    # Minimum quantity to buy
                    minimum_quantity = min_notional/price_on_bin  * 1.02
                    min_qty = self.round_up_to_ceil_with_precision(minimum_quantity, quantity_precision_integer)
                else:
                    print(f"Symbol {symbol} not found in exchange information.")
                    return 1002, f"Symbol {symbol} not found in exchange information."  # Error code and description , above we used 1005 and its same error check
            except Exception as e:
                print(f"Error occurred during coin info fetching from Binance or min_qty calculation.\nException:{traceback.format_exc()}")
                return 1003, f"Error occurred during coin info fetching from Binance or min_qty calculation.\nException: {e}"


            # Price difference checking
            price_ratio = (asset_price / price_on_bin)
            if not (1 + price_difference_ratio) >= price_ratio >= (1 - price_difference_ratio):
                print(f"Coin {symbol} prices differ by {price_difference_ratio * 100}%, so we are not taking the trade.")
                return 1004, f"Coin {symbol} prices differ by {price_difference_ratio * 100}%, so we are not taking the trade."


            # Setting leverage on binance for the coin
            try:
                response = client.futures_change_leverage(symbol=symbol, leverage=our_leverage)
                print(f"Leverage set to {our_leverage} for {symbol}. Response:{response}")
            except Exception as e:
                print(f"Error occurred during leverage setting on Binance.\nException: {traceback.format_exc()}")
                return 1005, f"Error occurred during leverage setting on Binance.\nException: {e}"


            # Get account information
            try:
                account_info = client.futures_account()
                available_balance = float(account_info['availableBalance'])
                print(f"**Available balance: {available_balance}")
            except Exception as e:
                print(f"Error occurred during available balance fetching from Binance.\nException: {traceback.format_exc()}")
                return 1006, f"Error occurred during available balance fetching from Binance.\nException: {e}"


            # threshold_balance
            if available_balance < threshold_balance:  # Checking minimum
                print(f"Available balance is less than Threshold_Balance:{threshold_balance}, so rejecting the open trade.")
                return 1007, f"Available balance is less than Threshold_Balance:{threshold_balance}, so rejecting the open trade."

            weighted_score_ratio = traders_list['Ranking_Score'][traders_list['account'] == address].iloc[0] / traders_list['Ranking_Score'].sum()
            leads_max_volume = traders_list['max_volume'][traders_list['account'] == address].iloc[0]
            
            print(f"weighted_score_ratio: {weighted_score_ratio}")
            print(f"leads_max_volume: {leads_max_volume}")

            #Calculating volume ratio in case volume ratio goes above 1
            if transaction_amount > leads_max_volume:
                volume_ratio = 1
            else:
                volume_ratio = (transaction_amount / leads_max_volume)
            print(f"volume_ratio: {volume_ratio}")


            # Collateral to invest main
            collateral_to_invest = (available_balance) * (weighted_score_ratio) * (volume_ratio) * (investement_risk_factor)

            
            print("min_qty :",min_qty)
            print("weighted_score_ratio :",weighted_score_ratio)
            print("volume_ratio :",volume_ratio)
            print("collateral_to_invest :",collateral_to_invest)
            
            
            # Calculating quantity to buy with precision
            total_usd_investment = (our_leverage * collateral_to_invest)
            print("total_usd_investment: ",total_usd_investment)
            ideal_quantity = (total_usd_investment / price_on_bin)
            print("ideal_quantity: ",ideal_quantity)
            if ideal_quantity < min_qty:
                # if (ideal_quantity / min_qty) > 0.60:
                print(f"Buying :{min_qty} allowed as (ideal_quantity:{ideal_quantity} < min_qty:{min_qty}).")
                quantity = min_qty 
                # else:
                    # print(f"Cannot buy quantity (={ideal_quantity}) of coin less than min_qty:{min_qty} allowed.")
                    # return 1008, f"Cannot buy quantity (={ideal_quantity}) of coin less than min_qty:{min_qty} allowed."
            else:
                quantity = self.round_up_to_ceil_with_precision(ideal_quantity, quantity_precision_integer)       # check
                print("quantity :", quantity)
            

            # Rechecking old stop loss and filling df if executed                                            # what if no stop loss exist check new
            response_from_old_stop_loss = self.check_old_stop_loss(client, trading_data_df, address, symbol, position_side) 
            print('Trying to check old stop loss status before moving on.')
            if response_from_old_stop_loss == False:
                print(f"Exception happened while check_old_stop_loss.")
                return False, f"Exception happened while check_old_stop_loss."


            # Now check the last row through below function & fetch last row values from Trading_df about the current position
            leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)


            # ------------------------- TAKING TRADE:
            # Getting side for trades
            open_side, close_side = self.sideAndCounterSideForBinance(position_side)

            # Try to palce order for upto number_of_try times
            for i in range(number_of_try):
                try:
                    market_order = client.futures_create_order(symbol=symbol, positionSide=position_side, side = open_side, type=client.FUTURE_ORDER_TYPE_MARKET, quantity=quantity)

                    market_orderId = str(market_order['orderId']) # Assigning orderid in string format.

                    current_trade_orderId = market_orderId

                    print("Market open trade order placed successfully. market_orderId: ",market_orderId)
                    break

                except Exception as e: #Error when 3rd try is not successful
                    print("Error placing order:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying placing market order in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while placing market open trade order.\nException: {traceback.format_exc()}")
                        return 1009, f"Error occurred while placing market open trade order.\nException: {e}"
                    
            time.sleep(retry_time)        
            # Trying to check market open trade order status n number of times.
            print("Checking market open trade order status if FILLED or NOT.")
            for i in range(number_of_try):
                try:
                    order_status = client.futures_get_order(
                        symbol=symbol,
                        orderId= market_orderId
                        )

                    if order_status['status'] == "FILLED":       # check new , earlier orderStatus SUCCESS was written, 'status': 'FILLED', or 'NEW'
                        print(f"Market open order status is FILLED, orderId: {order_status['orderId']}")
                        break
                    else:
                        if i <= (number_of_try - 2):
                            print(f"Market open order status is NOT FILLED. orderId: {order_status['orderId']}")
                            print(f"Retrying checking order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Market open order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close it manually if status id FILLED).")
                            return 1010, f"Market open order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close it manually if status id FILLED)."
                            
                except Exception as e: #Error when 3rd try is not successful
                    print("Error checking order status:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while checking status of market open trade order.\nException: {traceback.format_exc()}")
                        return 1011, f"Error occurred while checking status of market open trade order.\nException: {e}"

            marketOrderQty, marketOrderPrice = float(order_status['executedQty']), float(order_status['avgPrice'])
            new_our_transaction_amount = marketOrderQty * marketOrderPrice
            print("marketOrderQty: ", marketOrderQty)
            print("marketOrderPrice: ", marketOrderPrice)
            
            # Calculating new total holds & avg coin price
            new_leads_total_hold = round((transaction_quantity + leads_total_hold), quantity_precision_integer)   # coins
            new_leads_total_investment = (transaction_amount + leads_total_investment)
            new_avg_leads_coin_price = (new_leads_total_investment) / (new_leads_total_hold) 
            new_our_total_hold = round((marketOrderQty + our_total_hold), quantity_precision_integer)             # coins
            new_our_total_investment = (new_our_transaction_amount) + (our_total_investment)
            new_avg_coin_price = ((new_our_transaction_amount) + (our_total_investment)) / (new_our_total_hold)
            new_total_hold_ratio = (new_our_total_hold / new_leads_total_hold)

            print(f"new_leads_total_hold: {new_leads_total_hold}")
            print(f"new_leads_total_investment: {new_leads_total_investment}")
            print(f"new_avg_leads_coin_price: {new_avg_leads_coin_price}")
            print(f"new_our_total_hold: {new_our_total_hold}")
            print(f"new_our_total_investment: {new_our_total_investment}")
            print(f"new_avg_coin_price: {new_avg_coin_price}")
            print(f"new_total_hold_ratio: {new_total_hold_ratio}")

            # ------------ Resetting Stoploss
            # Try to cancel_older_stoploss for upto number_of_try times
            if stop_loss_order_id is not None:
                print(f"Old stoploss orderId: {stop_loss_order_id}")
                print('Trying to cancel old stop loss')
                for i in range(number_of_try):  
                    try:
                        cancel_older_stoploss = client.futures_cancel_order(symbol=symbol, orderId=stop_loss_order_id)

                        canceled_order_orderId = str(cancel_older_stoploss['orderId']) # Assigning orderid in string format.
                        print("Older stoploss cancelation order placed successfully.")
                        break

                    except Exception as e: #Error when 3rd try is not successful
                        print("Error canceling older stoploss order:", e)
                        if i <= (number_of_try - 2): 
                            print(f"Retrying cancel_older_stoploss in {retry_time} seconds...(try no: {i}/{number_of_try})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Exception happened while canceling old stop_loss.\nException: {traceback.format_exc()}")
                            return 1011, f"Exception happened while canceling old stop_loss.\nException: {e}"
                time.sleep(retry_time)
                #Checking cancelation status n number of time
                for i in range(number_of_try): 
                    try:                    
                        order_status_stop_loss = client.futures_get_order(   # check new
                            symbol=symbol,
                            orderId= canceled_order_orderId
                        )
                        if order_status_stop_loss['status'] == "CANCELED":
                            print(f"Stoploss order status is CANCELED. orderID: {order_status_stop_loss['orderId']}")
                            break
                        else:
                            if i <= (number_of_try - 2):
                                print(f"Stoploss order cancelation status is NOT CANCELED. orderID: {order_status_stop_loss['orderId']}")
                                print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                time.sleep(retry_time)
                                continue
                            else:
                                print(f"Stoploss order cancelation status is NOT CANCELED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED).")
                                return 1010, f"Stoploss order cancelation status is NOT CANCELED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED)."

                    except Exception as e: #Error when 3rd try is not successful
                        print("Error checking cancelation order status:", e)
                        if i <= (number_of_try - 2):
                            print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Error occurred while checking status of older stop_loss cancelation order.\nException: {traceback.format_exc()}")
                            return 1011, f"Error occurred while checking status of older stop_loss cancelation order.\nException: {e}"
                        
            else:
                print("Older stop_loss_order_id was None. No cancellation needed")



            #------------------ Placing Stoploss order
            info = None

            # Using new_leads_leverage_for_stoploss, as new_leads_leverage can be sometimes very low and we cannot allot money that much over out actual leverage our_leverage, also calcualtions will get stop price 0 or negative if new leads leerage is 1 or less.
            if new_leads_leverage < min_leverage_for_stop_price:
                print(f"As new_leads_leverage({new_leads_leverage}) < min_leverage_for_stop_price({min_leverage_for_stop_price}), taking (new_leads_leverage = min_leverage_for_stop_price)")
                new_leads_leverage_for_stoploss = min_leverage_for_stop_price
            elif new_leads_leverage > max_leverage_for_stop_price:
                print(f"As new_leads_leverage({new_leads_leverage}) > max_leverage_for_stop_price({max_leverage_for_stop_price}), taking (new_leads_leverage = max_leverage_for_stop_price)")
                new_leads_leverage_for_stoploss = max_leverage_for_stop_price
            else:
                new_leads_leverage_for_stoploss = new_leads_leverage

            
            x = 1 if position_side == "LONG" else -1
            print('Trying to place stop loss')
            stoploss_percent = percent_we_can_loose_stop_loss                         # Not using it anymore
            new_stop_loss_price = round((new_avg_coin_price - (new_avg_coin_price / new_leads_leverage_for_stoploss) * (x)), price_precision_integer) # using new_leads_leverage_for_stoploss, as new_leads_leverage can be sometime very low and we cannot allot money that much over out actual leverage our_leverage.
            print(f"new_stop_loss_price: {new_stop_loss_price}")

            # Try to place stop_loss_order for up to number_of_try times
            for i in range(number_of_try):
                try:
                    stop_loss_order = client.futures_create_order(symbol=symbol, positionSide=position_side, side=close_side,
                                                            type=client.FUTURE_ORDER_TYPE_STOP_MARKET,
                                                            quantity=new_our_total_hold,
                                                            stopPrice=new_stop_loss_price)

                    stop_loss_orderId = str(stop_loss_order['orderId']) # Assigning orderid in string format.
                    print("Stoploss order placed successfully. stop_loss_orderId: ", stop_loss_orderId)
                    break
                    
                except Exception as e:

                    if hasattr(e, 'code') and e.code == -2021:
                        print(f"Order would Immediately trigger error encountered.\nException: {e}")
                        print("Closing complete position immediately.")
                        # Immediately close the postiion.
                        # Try to place stop_loss_market_order for upto number_of_try times
                        for i in range(number_of_try):
                            try:
                                stop_loss_market_order = client.futures_create_order(symbol=symbol, positionSide=position_side,
                                                                                side=close_side,
                                                                                type=client.FUTURE_ORDER_TYPE_MARKET,
                                                                                quantity=new_our_total_hold)
                                
                                stop_loss_orderId = str(stop_loss_market_order['orderId']) # Assigning orderid in string format.
                                print("Stoploss market order placed successfully. stop_loss_orderId: ", stop_loss_orderId)
                                break
                                
                            except Exception as e: #Error when 3rd try is not successful
                                print("Error placing stop_loss_market_order:", e)
                                if i <= (number_of_try - 2):           #--------------------- check
                                    print(f"Retrying stop_loss_market_order in {retry_time} seconds...(try no: {i}/{number_of_try})")
                                    time.sleep(retry_time)
                                    continue
                                else:
                                    stop_loss_orderId = None
                                    print(f"Error occurred while placing stoploss_market_order also.\nException: {traceback.format_exc()}")
                                    return 1012, f"Error occurred while placing stoploss_market_order ordern also.\nException: {e}"
                        time.sleep(retry_time)        
                        for i in range(number_of_try):
                            try:    
                                order_status_stop_loss_market_order = client.futures_get_order(   # check new
                                    symbol = symbol,
                                    orderId = stop_loss_orderId)
                                
                                if order_status_stop_loss_market_order['status'] == "FILLED":
                                    print(f"Stoploss market order is FILLED for: {order_status_stop_loss_market_order['orderId']}")
                                    info = "stop_loss_error"
                                    break
                                else:
                                    if i <= (number_of_try - 2):
                                        print(f"Stoploss market order status is NOT FILLED. orderID: {order_status_stop_loss_market_order['orderId']}")
                                        print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                        time.sleep(retry_time)
                                        continue
                                    else:
                                        print(f"Stoploss market order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id FILLED).")
                                        return 1010, f"Stoploss market order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id FILLED)."

                                
                            except Exception as e: #Error when 3rd try is not successful
                                print("Error checking cancelation order status:", e)
                                if i <= (number_of_try - 2):
                                    print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                                    time.sleep(retry_time)
                                    continue
                                else:
                                    print(f"Error occurred while checking status of Stoploss market order.\nException: {traceback.format_exc()}")
                                    return 1011, f"Error occurred while checking status of Stoploss market order.\nException: {e}"
            
                        # Calculations with new data
                        stopmarketOrderQty, stopmarketOrderPrice = float(order_status_stop_loss_market_order['executedQty']), float(order_status_stop_loss_market_order['avgPrice'])
                        stopmarket_our_transaction_amount = (stopmarketOrderQty) * (stopmarketOrderPrice)
                        # PNL Calculation
                        y = 1 if position_side == "LONG" else -1
                        stop_PNL = stopmarketOrderQty * (stopmarketOrderPrice - new_avg_coin_price) * (y)                                      
                        print(f"stop_PNL: {stop_PNL}")
                        break 

                    elif i <= (number_of_try - 2):                     #--------------------- check
                        print(f"Retrying to place stop_loss_order in {retry_time} seconds...(try no: {i}/{number_of_try})")
                        time.sleep(retry_time)
                        continue
                    
                    else:
                        print(f"Exception happened while placing stop_loss_order after 3rd attempt also.\nException: {traceback.format_exc()}")
                        return 1022, f"Exception happened while placing stop_loss_order after 3rd attempt also.\nException: {e}"
            time.sleep(retry_time)
            if info == None:
                for i in range(number_of_try):
                    try:
                        order_status_stop_loss = client.futures_get_order(   # check new
                            symbol = symbol,
                            orderId = stop_loss_orderId
                        )
                        if order_status_stop_loss['status'] == "NEW":       # check new
                            print(f"Stoploss order status is NEW. orderId: {order_status_stop_loss['orderId']}")
                            break  # Exit the loop if order is placed successfully
                        else:
                            if i <= (number_of_try - 2):
                                print(f"Stoploss order status is NOT NEW. orderID: {order_status_stop_loss['orderId']}")
                                print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                time.sleep(retry_time)
                                continue
                            else:
                                print(f"Stoploss order status is NOT NEW after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED).")
                                return 1010, f"Stoploss order status is NOT NEW after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED)."
                            
                    except Exception as e: #Error when 3rd try is not successful
                        print("Error checking cancelation order status:", e)
                        if i <= (number_of_try - 2):
                            print(f"Retrying checking order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Error occurred while checking status of older stop_loss cancelation order.\nException: {traceback.format_exc()}")
                            return 1011, f"Error occurred while checking status of older stop_loss cancelation order.\nException: {e}"


            # Append new row in the Trading_df with all updated details details.
            self.add_to_trading_data_df(
                time=self.get_current_time(),
                trade_order_id=market_orderId,
                address=address, 
                symbol=symbol, 
                is_long_short=position_side,
                trade_type=open_side,
                leads_price=asset_price,
                price=marketOrderPrice,
                weighted_score_ratio=weighted_score_ratio,
                leads_max_volume=leads_max_volume,
                leads_leverage=new_leads_leverage,
                leads_transaction_quantity=transaction_quantity,
                leads_transaction_amount=transaction_amount,
                our_leverage=our_leverage,
                our_transaction_quantity=marketOrderQty,
                our_transaction_amount=new_our_transaction_amount,
                leads_total_hold=new_leads_total_hold, 
                leads_total_investment=new_leads_total_investment,
                avg_leads_coin_price=new_avg_leads_coin_price,
                our_total_hold=new_our_total_hold,
                our_total_investment=new_our_total_investment,
                avg_coin_price=new_avg_coin_price,
                total_hold_ratio=new_total_hold_ratio,
                stop_loss_price=new_stop_loss_price,
                stop_loss_order_id=stop_loss_orderId,
                is_stop_loss_executed=False,
                is_liquidated=False,
                take_profit_price=0,
                take_profit_order_id=None,
                PNL=0
            )


            # If error happened during placing the general stop_loss order
            if info == "stop_loss_error":  # this means stop_loss price conflicted with market price and we have sold the coins immediately.
                self.add_to_trading_data_df(
                    time= self.get_current_time(),
                    trade_order_id=stop_loss_orderId,
                    address=address,
                    symbol=symbol,
                    is_long_short=position_side,
                    trade_type=close_side,
                    leads_price=0,
                    price=stopmarketOrderPrice,
                    weighted_score_ratio=weighted_score_ratio,
                    leads_max_volume=leads_max_volume,
                    leads_leverage=new_leads_leverage,
                    leads_transaction_quantity=0,
                    leads_transaction_amount=0,
                    our_leverage=our_leverage,
                    our_transaction_quantity=stopmarketOrderQty,
                    our_transaction_amount=stopmarket_our_transaction_amount,
                    leads_total_hold=0, 
                    leads_total_investment=0,
                    avg_leads_coin_price=0,
                    our_total_hold=0,
                    our_total_investment=new_our_total_investment,
                    avg_coin_price=new_avg_coin_price,
                    total_hold_ratio=0,
                    stop_loss_price=0,
                    stop_loss_order_id=None,
                    is_stop_loss_executed=True,
                    is_liquidated=False,
                    take_profit_price=0,
                    take_profit_order_id=None,
                    PNL=stop_PNL
                )

            # Return the code as True and error description as None if everything goes succesfully
            return True, None


        collector = Collector()
        collector.start_collecting()

        response, description = openTrade( client, traders_list, address, symbol, position_side, asset_price, transaction_amount, transaction_quantity, new_leads_leverage)

        collector.stop_collecting()
        content_prints = collector.content

        if response == True:
            pass
        else:
            if current_trade_orderId is not None:
                Alert_note = f"Panic, Open (in ultimate_openTrade fucntion) trade taken before error(Now banning the position for {ban_time_hours}hrs). current_trade_orderId:{current_trade_orderId}"
                current_market_OrderQty, current_market_OrderPrice, new_our_total_hold, new_avg_coin_price, market_order_status = self.error_return_latest_data(address, symbol, position_side, current_trade_orderId, client)
                #Writing content for email
                print(Alert_note)
                content = f"{Alert_note}\nError code: {response},\nDescription: {description},\n\naddress: {address},\ncoin:{coin},\nis_long_short: {position_side},\ntime: {self.get_current_time()},\ntransaction_quantity: {transaction_quantity},\ntransaction_amount: {transaction_amount}\n\ncurrent_market_OrderQty:{current_market_OrderQty}, current_market_OrderPrice:{current_market_OrderPrice}, new_our_total_hold:{new_our_total_hold}, new_avg_coin_price:{new_avg_coin_price},\nmarket_order_status:{market_order_status}\n\n\n{content_prints}"
                self.send_message("ALERT", content)
                self.add_to_ban_list(address, symbol, position_side, current_trade_orderId, current_market_OrderQty, current_market_OrderPrice, new_our_total_hold, new_avg_coin_price) # Added to "ban_positions_info_list"
            else:
                Alert_note = "Relax, Open (in ultimate_openTrade fucntion) trade not taken before error"
                leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)
                #Writing content for email
                print(Alert_note)
                content = f"{Alert_note}\nError code: {response},\nDescription: {description},\n\naddress: {address},\ncoin:{coin},\nis_long_short: {position_side},\ntime: {self.get_current_time()},\ntransaction_quantity: {transaction_quantity},\ntransaction_amount: {transaction_amount}\n,\nour_total_hold:{our_total_hold},\navg_coin_price:{avg_coin_price}\n\n\n\n{content_prints}"
                self.send_message("ALERT", content)




#---Closing----------
    def ultimate_closeTrade(self, client, traders_list, address, coin, position_side, asset_price, transaction_amount, transaction_quantity, new_leads_leverage):

        print("Time:", self.get_current_time())

        symbol = coin + "USDT"
        current_trade_orderId = None

        # Closing Trades
        def closeTrade(client, address, symbol, position_side, asset_price, transaction_amount, transaction_quantity, new_leads_leverage):


            PNL = 0
            stop_PNL = 0
            nonlocal current_trade_orderId
            
            weighted_score_ratio = traders_list['Ranking_Score'][traders_list['account'] == address].iloc[0] / traders_list['Ranking_Score'].sum()
            leads_max_volume = traders_list['max_volume'][traders_list['account'] == address].iloc[0]

            #---------------------------
            try:                                                                                                                     #  added new check
                exchange_information = client.futures_exchange_info()
                symbol_info = next((s for s in exchange_information['symbols'] if s['symbol'] == symbol), None)  # corrected line
                if symbol_info:
                    # Precision for the quantity
                    quantity_precision = next((f['stepSize'] for f in symbol_info['filters'] if f['filterType'] == 'MARKET_LOT_SIZE'), None)
                    # Precision for the price in dollar
                    price_precision =  next((f['tickSize'] for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
                    # Minimum notional value(minimum dollars)
                    min_notional = float(next((f['notional'] for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None))
                    # Get integer value of precision
                    quantity_precision_integer = 0 if '.' not in str(quantity_precision) else len(
                        str(quantity_precision).split('.')[1].rstrip('0')) if str(quantity_precision) else None
                    price_precision_integer = 0 if '.' not in str(price_precision) else len(
                        str(price_precision).split('.')[1].rstrip('0')) if str(price_precision) else None

                    #Printing lead's qunatity and amount
                    transaction_amount = float(self.floor_decimal(transaction_amount, price_precision_integer))
                    transaction_quantity = float(self.floor_decimal(transaction_quantity, quantity_precision_integer))
                    print(f"Lead's transaction amaount: ", transaction_amount)
                    print(f"Lead's transaction quantity: ", transaction_quantity)
                    if transaction_amount == 0 or transaction_quantity == 0:
                        print("Lead's Quantites are zero when rounded. Rejecting trade.")
                        return True, None
                    print(f"min_notional: {min_notional}")
                    print(f"quantity_precision_integer: {quantity_precision_integer}")
                    print(f"price_precision_integer: {price_precision_integer}")
                    
                    quantity_precision_integer = int(quantity_precision_integer)
                    price_precision_integer = int(price_precision_integer)
                    
                    try:                                                                                             #  added new check
                        ticker = client.futures_symbol_ticker(symbol=symbol)
                        price_on_bin = float(ticker['price'])
                        print(f"Current market price of {symbol}: {price_on_bin}")
                    except Exception as e:
                        print(f"Error occurred during coin {symbol} price fetching from Binance.\nException: {traceback.format_exc()}")
                        return 2001, f"Error occurred during coin {symbol} price fetching from Binance.\nException: {e}"
                    
                    # Minimum quantity to buy
                    minimum_quantity = min_notional / price_on_bin * 1.02
                    min_qty = self.round_up_to_ceil_with_precision(minimum_quantity, quantity_precision_integer)
                    
                else:
                    print(f"Symbol {symbol} not found in exchange information.")
                    return 2002, f"Symbol {symbol} not found in exchange information."  # Error code and description , above we used 1005 and its same error check
                
            except Exception as e:
                print(f"Error occurred during coin info fetching from Binance.\nException: {traceback.format_exc()}")
                return 2003, f"Error occurred during coin info fetching from Binance.\nException: {e}"

            
            # Rechecking old stop loss and filling df if executed
            response_from_old_stop_loss = self.check_old_stop_loss(client, trading_data_df, address, symbol, position_side) 
            print('Trying to check old stop loss status before moving on.')
            if response_from_old_stop_loss == False:
                print(f"Exception happened while check_old_stop_loss.")
                return False, f"Exception happened while check_old_stop_loss."


            # Now check the last row through below function & fetch last row values from Trading_df about the current position
            leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)


            # Check if the trader had any last row present that is able to let us close it
            if our_total_hold == 0:  # As ultimately if last row was not present or was not eligible, we return our_total_hold=0
                print("No asset or open-position present to close")
                return True, "No asset or open-position present to close"  # Error code and description
            else:
                pass


            #-------------------------------------------------
            # Calculating parameters for closing                                          
            if transaction_quantity >= leads_total_hold:
                quantity_to_close = our_total_hold
                print("--Closing completely.--")
            else:
                quantity_to_close = round((total_hold_ratio * transaction_quantity), quantity_precision_integer)
                print("ideal_quantity_to_close: ",quantity_to_close)
                min_qty_to_close = 1/(10**(quantity_precision_integer)) #For closing, minimum quantity is equal to lowest number in precesion possible.
                if quantity_to_close >= our_total_hold:
                    quantity_to_close = our_total_hold
                elif quantity_to_close > 0.98 * our_total_hold:
                    quantity_to_close = our_total_hold
                elif quantity_to_close < min_qty_to_close:
                    quantity_to_close = min_qty_to_close
                

            print(f"Our hold: {our_total_hold}")
            print(f"Quantity to close: {quantity_to_close}")


            # Fetching open_side value i.e buy or sell
            open_side, close_side = self.sideAndCounterSideForBinance(position_side)


            # Try to palce order for upto number_of_try times
            #Clsoing order market.
            for i in range(number_of_try):
                try:
                    market_order = client.futures_create_order(symbol=symbol, positionSide=position_side, side=close_side,
                                            type=client.FUTURE_ORDER_TYPE_MARKET, quantity=quantity_to_close)

                    market_orderId = str(market_order['orderId']) # Assigning orderid in string format.

                    current_trade_orderId = market_orderId
                    
                    print("Market close trade order placed successfully. market_orderId: ", market_orderId)
                    break

                except Exception as e: #Error when 3rd try is not successful
                    print("Error placing order:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying placing market order in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while placing market close trade order.\nException: {traceback.format_exc()}")
                        return 1009, f"Error occurred while placing market close trade order.\nException: {e}"

            time.sleep(retry_time)        
            # Trying to check market close trade order status n number of times.
            print("Checking market close trade order status if FILLED or NOT.")
            for i in range(number_of_try):
                try:
                    order_status = client.futures_get_order(
                        symbol=symbol,
                        orderId= market_orderId
                        )

                    if order_status['status'] == "FILLED":       # check new , earlier orderStatus SUCCESS was written, 'status': 'FILLED', or 'NEW'
                        print(f"Market close order status is FILLED, orderId: {market_order['orderId']}")
                        break
                    else:
                        if i <= (number_of_try - 2):
                            print(f"Market close order status is NOT FILLED. orderId: {market_order['orderId']}")
                            print(f"Retrying checking order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Market close order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close it manually if status id FILLED).")
                            return 1010, f"Market close order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close it manually if status id FILLED)."
                            
                except Exception as e: #Error when 3rd try is not successful
                    print("Error checking order status:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while checking status of market close trade order.\nException: {traceback.format_exc()}")
                        return 1011, f"Error occurred while checking status of market closeopen trade order.\nException: {e}"


            marketOrderQty, marketOrderPrice = float(order_status['executedQty']), float(order_status['avgPrice'])
            new_our_transaction_amount = marketOrderQty * marketOrderPrice

            # PNL
            y = 1 if position_side == "LONG" else -1
            PNL = marketOrderQty * (marketOrderPrice - avg_coin_price) * (y)                                         # check
            print(f"PNL: {PNL}")

            # Calculating leads values
            if (transaction_quantity >= leads_total_hold) or (quantity_to_close == our_total_hold):
                new_leads_total_hold = 0
                new_leads_total_investment = 0
            else:
                new_leads_total_hold =  round((leads_total_hold - transaction_quantity), quantity_precision_integer)   # coins
                new_leads_total_investment = (leads_total_investment - transaction_amount)
            new_avg_leads_coin_price = avg_leads_coin_price

            # Calculating out values
            new_our_total_hold = round((our_total_hold - marketOrderQty), quantity_precision_integer)             # coins
            if new_our_total_hold != 0:
                new_our_total_investment = (our_total_investment) - (new_our_transaction_amount)
            else:
                new_our_total_investment = 0
            new_avg_coin_price = avg_coin_price
            new_total_hold_ratio = total_hold_ratio

            print(f"new_leads_total_hold: {new_leads_total_hold}")
            print(f"new_leads_total_investment: {new_leads_total_investment}")
            print(f"new_avg_leads_coin_price: {new_avg_leads_coin_price}")
            print(f"new_our_total_hold: {new_our_total_hold}")
            print(f"new_our_total_investment: {new_our_total_investment}")
            print(f"new_avg_coin_price: {new_avg_coin_price}")
            print(f"new_total_hold_ratio: {new_total_hold_ratio}")

            # ------------ Resetting Stoploss
            # Try to cancel_older_stoploss for upto number_of_try times
            if stop_loss_order_id is not None:
                print(f"Old stoploss orderId: {stop_loss_order_id}")
                print('Trying to cancel old stop loss')
                for i in range(number_of_try):  
                    try:
                        cancel_older_stoploss = client.futures_cancel_order(symbol=symbol, orderId=stop_loss_order_id)

                        canceled_order_orderId = str(cancel_older_stoploss['orderId']) # Assigning orderid in string format.
                        print("Older stoploss cancelation order placed successfully.")
                        break

                    except Exception as e: #Error when 3rd try is not successful
                        print("Error canceling older stoploss order:", e)
                        if i <= (number_of_try - 2): 
                            print(f"Retrying cancel_older_stoploss in {retry_time} seconds...(try no: {i}/{number_of_try})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Exception happened while canceling old stop_loss.\nException: {traceback.format_exc()}")
                            return 1011, f"Exception happened while canceling old stop_loss.\nException: {e}"
                time.sleep(retry_time)
                #Checking cancelation status n number of time
                for i in range(number_of_try): 
                    try:                    
                        order_status_stop_loss = client.futures_get_order(   # check new
                            symbol=symbol,
                            orderId= canceled_order_orderId
                        )
                        if order_status_stop_loss['status'] == "CANCELED":
                            print(f"Stoploss order status is CANCELED. orderID: {order_status_stop_loss['orderId']}")
                            break
                        else:
                            if i <= (number_of_try - 2):
                                print(f"Stoploss order cancelation status is NOT CANCELED. orderID: {order_status_stop_loss['orderId']}")
                                print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                time.sleep(retry_time)
                                continue
                            else:
                                print(f"Stoploss order cancelation status is NOT CANCELED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED).")
                                return 1010, f"Stoploss order cancelation status is NOT CANCELED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED)."

                    except Exception as e: #Error when 3rd try is not successful
                        print("Error checking cancelation order status:", e)
                        if i <= (number_of_try - 2):
                            print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Error occurred while checking status of older stop_loss cancelation order.\nException: {traceback.format_exc()}")
                            return 1011, f"Error occurred while checking status of older stop_loss cancelation order.\nException: {e}"
                        
            else:
                print("Older stop_loss_order_id was None. Not possible, as our_hold was not zero, i.e old stoploss should be their.") # Not expected to ever come to this part if older stoploss was not there, as if stoploss was not there i.e our_hold must be 0, so trade should be rejected in before condition.
                return 2023, "Older stop_loss_order_id was None. Not possible, as our_hold was not zero, i.e old stoploss should be their."
        

        #-------------------------------------------------------------------------------------------
            # Now place new stop-loss with updated coin quantityand price after cancelling older stop_loss
            # Calculating new total holds & new avg coin price
            info = None
            stop_loss_orderId = None # Initializing the variable
            new_stop_loss_price = None


                
            if new_our_total_hold !=0:
                
                # Using new_leads_leverage_for_stoploss, as new_leads_leverage can be sometimes very low and we cannot allot money that much over out actual leverage our_leverage, also calcualtions will get stop price 0 or negative if new leads leerage is 1 or less.
                if new_leads_leverage < min_leverage_for_stop_price:
                    print(f"As new_leads_leverage({new_leads_leverage}) < min_leverage_for_stop_price({min_leverage_for_stop_price}), taking (new_leads_leverage = min_leverage_for_stop_price)")
                    new_leads_leverage_for_stoploss = min_leverage_for_stop_price
                elif new_leads_leverage > max_leverage_for_stop_price:
                    print(f"As new_leads_leverage({new_leads_leverage}) > max_leverage_for_stop_price({max_leverage_for_stop_price}), taking (new_leads_leverage = max_leverage_for_stop_price)")
                    new_leads_leverage_for_stoploss = max_leverage_for_stop_price
                else:
                    new_leads_leverage_for_stoploss = new_leads_leverage

                
                x = 1 if position_side == "LONG" else -1
                stoploss_percent = percent_we_can_loose_stop_loss  # it is the amount ratio we are ready to lose
                new_stop_loss_price = round((new_avg_coin_price - (new_avg_coin_price / new_leads_leverage_for_stoploss) * (x)), price_precision_integer) # using new_leads_leverage_for_stoploss, as new_leads_leverage can be sometime very low and we cannot allot money that much over out actual leverage our_leverage.
                print(f"new_stop_loss_price: {new_stop_loss_price}")
                print('Trying to place stop loss')

                # Try to place stop_loss_order for up to number_of_try times
                for i in range(number_of_try):
                    try:
                        stop_loss_order = client.futures_create_order(symbol=symbol, positionSide=position_side, side=close_side,
                                                                type=client.FUTURE_ORDER_TYPE_STOP_MARKET,
                                                                quantity=new_our_total_hold,
                                                                stopPrice=new_stop_loss_price)

                        stop_loss_orderId = str(stop_loss_order['orderId']) # Assigning orderid in string format.
                        print("Stoploss order placed successfully. stop_loss_orderId: ", stop_loss_orderId)
                        break
                        
                    except Exception as e:

                        if hasattr(e, 'code') and e.code == -2021:
                            print(f"Order would Immediately trigger error encountered.\nException: {e}")
                            print("Closing complete position immediately.")
                            # Immediately close the postiion.
                            # Try to place stop_loss_market_order for upto number_of_try times
                            for i in range(number_of_try):
                                try:
                                    stop_loss_market_order = client.futures_create_order(symbol=symbol, positionSide=position_side,
                                                                                    side=close_side,
                                                                                    type=client.FUTURE_ORDER_TYPE_MARKET,
                                                                                    quantity=new_our_total_hold)
                                    
                                    stop_loss_orderId = str(stop_loss_market_order['orderId']) # Assigning orderid in string format.
                                    print("Stoploss market order placed successfully. stop_loss_orderId: ", stop_loss_orderId)
                                    break
                                    
                                except Exception as e: #Error when 3rd try is not successful
                                    print("Error placing stop_loss_market_order:", e)
                                    if i <= (number_of_try - 2):           #--------------------- check
                                        print(f"Retrying stop_loss_market_order in {retry_time} seconds...(try no: {i}/{number_of_try})")
                                        time.sleep(retry_time)
                                        continue
                                    else:
                                        stop_loss_orderId = None
                                        print(f"Error occurred while placing stoploss_market_order also.\nException: {traceback.format_exc()}")
                                        return 1012, f"Error occurred while placing stoploss_market_order ordern also.\nException: {e}"
                            time.sleep(retry_time)        
                            for i in range(number_of_try):
                                try:    
                                    order_status_stop_loss_market_order = client.futures_get_order(   # check new
                                        symbol = symbol,
                                        orderId = stop_loss_orderId)
                                    
                                    if order_status_stop_loss_market_order['status'] == "FILLED":
                                        print(f"Stoploss market order is FILLED for: {order_status_stop_loss_market_order['orderId']}")
                                        info = "stop_loss_error"
                                        break
                                    else:
                                        if i <= (number_of_try - 2):
                                            print(f"Stoploss market order status is NOT FILLED. orderID: {order_status_stop_loss_market_order['orderId']}")
                                            print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                            time.sleep(retry_time)
                                            continue
                                        else:
                                            print(f"Stoploss market order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id FILLED).")
                                            return 1010, f"Stoploss market order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id FILLED)."

                                    
                                except Exception as e: #Error when 3rd try is not successful
                                    print("Error checking cancelation order status:", e)
                                    if i <= (number_of_try - 2):
                                        print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                                        time.sleep(retry_time)
                                        continue
                                    else:
                                        print(f"Error occurred while checking status of Stoploss market order.\nException: {traceback.format_exc()}")
                                        return 1011, f"Error occurred while checking status of Stoploss market order.\nException: {e}"
                
                            # Calculations with new data
                            stopmarketOrderQty, stopmarketOrderPrice = float(order_status_stop_loss_market_order['executedQty']), float(order_status_stop_loss_market_order['avgPrice'])
                            stopmarket_our_transaction_amount = (stopmarketOrderQty) * (stopmarketOrderPrice)
                            # PNL Calculation
                            y = 1 if position_side == "LONG" else -1
                            stop_PNL = stopmarketOrderQty * (stopmarketOrderPrice - new_avg_coin_price) * (y)                                      
                            print(f"stop_PNL: {stop_PNL}")
                            break 

                        elif i <= (number_of_try - 2):                     #--------------------- check
                            print(f"Retrying to place stop_loss_order in {retry_time} seconds...(try no: {i}/{number_of_try})")
                            time.sleep(retry_time)
                            continue
                        
                        else:
                            print(f"Exception happened while placing stop_loss_order after 3rd attempt also.\nException: {traceback.format_exc()}")
                            return 1022, f"Exception happened while placing stop_loss_order after 3rd attempt also.\nException: {e}"
                time.sleep(retry_time)
                if info == None:
                    for i in range(number_of_try):
                        try:
                            order_status_stop_loss = client.futures_get_order(   # check new
                                symbol = symbol,
                                orderId = stop_loss_orderId
                            )
                            if order_status_stop_loss['status'] == "NEW":       # check new
                                print(f"Stoploss order status is NEW. orderId: {order_status_stop_loss['orderId']}")
                                break  # Exit the loop if order is placed successfully
                            else:
                                if i <= (number_of_try - 2):
                                    print(f"Stoploss order status is NOT NEW. orderID: {order_status_stop_loss['orderId']}")
                                    print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                    time.sleep(retry_time)
                                    continue
                                else:
                                    print(f"Stoploss order status is NOT NEW after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED).")
                                    return 1010, f"Stoploss order status is NOT NEW after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED)."

                        except Exception as e: #Error when 3rd try is not successful
                            print("Error checking cancelation order status:", e)
                            if i <= (number_of_try - 2):
                                print(f"Retrying checking order status in {retry_time} seconds...({i})")
                                time.sleep(retry_time)
                                continue
                            else:
                                print(f"Error occurred while checking status of older stop_loss cancelation order.\nException: {traceback.format_exc()}")
                                return 1011, f"Error occurred while checking status of older stop_loss cancelation order.\nException: {e}"


            # Append new row in the Trading_df with all updated details details.
            self.add_to_trading_data_df(
                time= self.get_current_time(),
                trade_order_id=market_orderId,
                address=address,
                symbol=symbol,
                is_long_short=position_side,
                trade_type=close_side,
                leads_price=asset_price,
                price=marketOrderPrice,
                weighted_score_ratio=weighted_score_ratio,
                leads_max_volume=leads_max_volume,
                leads_leverage=new_leads_leverage,
                leads_transaction_quantity=transaction_quantity,
                leads_transaction_amount=transaction_amount,
                our_leverage=our_leverage,
                our_transaction_quantity=marketOrderQty,
                our_transaction_amount=new_our_transaction_amount,
                leads_total_hold=new_leads_total_hold,
                leads_total_investment=new_leads_total_investment,
                avg_leads_coin_price=new_avg_leads_coin_price,
                our_total_hold=new_our_total_hold,
                our_total_investment=new_our_total_investment,
                avg_coin_price=new_avg_coin_price,
                total_hold_ratio=new_total_hold_ratio,
                stop_loss_price=new_stop_loss_price,
                stop_loss_order_id=stop_loss_orderId,
                is_stop_loss_executed=False,
                is_liquidated=False,
                take_profit_price=0,
                take_profit_order_id=None,
                PNL=PNL
            )

            # If error happened during palcing the general stop_loss order
            if info == "stop_loss_error":  # this means stop_loss price conflicted with market price and we have sold the coins immideately.
                self.add_to_trading_data_df(
                    time= self.get_current_time(),
                    trade_order_id=stop_loss_orderId,
                    address=address,
                    symbol=symbol,
                    is_long_short=position_side,
                    trade_type=close_side,
                    leads_price=0,
                    price=stopmarketOrderPrice,
                    weighted_score_ratio=weighted_score_ratio,
                    leads_max_volume=leads_max_volume,
                    leads_leverage=new_leads_leverage,
                    leads_transaction_quantity=0,
                    leads_transaction_amount=0,
                    our_leverage=our_leverage,
                    our_transaction_quantity=stopmarketOrderQty,
                    our_transaction_amount=stopmarket_our_transaction_amount,
                    leads_total_hold=0, 
                    leads_total_investment=0,
                    avg_leads_coin_price=new_avg_leads_coin_price,
                    our_total_hold=0,
                    our_total_investment=new_our_total_investment,
                    avg_coin_price=new_avg_coin_price,
                    total_hold_ratio=0,
                    stop_loss_price=0,
                    stop_loss_order_id=None,
                    is_stop_loss_executed=True,
                    is_liquidated=False,
                    take_profit_price=0,
                    take_profit_order_id=None,
                    PNL=stop_PNL
                )
            
            # Return the code as True and error description as None if everything goes succesfully
            return True, None 

        collector = Collector()
        collector.start_collecting()

        response, description = closeTrade(client, address, symbol, position_side, asset_price, transaction_amount, transaction_quantity, new_leads_leverage)

        collector.stop_collecting()
        content_prints = collector.content

        if response == True:
            pass
        else:
            if current_trade_orderId is not None:
                Alert_note = f"Panic, Close (ultimate_closeTrade function) trade taken before error(Now banning the position for {ban_time_hours}hrs). current_trade_orderId:{current_trade_orderId}"
                current_market_OrderQty, current_market_OrderPrice, new_our_total_hold, new_avg_coin_price, market_order_status = self.error_return_latest_data(address, symbol, position_side, current_trade_orderId, client)
                #Writing content for email
                print(Alert_note)
                content = f"{Alert_note}\nError code: {response},\nDescription: {description},\n\naddress: {address},\ncoin:{coin}, is_long_short: {position_side},\ntime: {self.get_current_time()},\ntransaction_quantity: {transaction_quantity},\ntransaction_amount: {transaction_amount}\n\ncurrent_market_OrderQty:{current_market_OrderQty},\ncurrent_market_OrderPrice:{current_market_OrderPrice},\nnew_our_total_hold:{new_our_total_hold},\nnew_avg_coin_price:{new_avg_coin_price},\nmarket_order_status:{market_order_status}\n\n\n{content_prints}"
                self.send_message("ALERT", content)
                self.add_to_ban_list(address, symbol, position_side, current_trade_orderId, current_market_OrderQty, current_market_OrderPrice, new_our_total_hold, new_avg_coin_price) # Added to "ban_positions_info_list"
            else:
                Alert_note = "Relax, Close (ultimate_closeTrade function) trade not taken before error"
                leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)
                #Writing content for email
                print(Alert_note)
                content = f"{Alert_note}\nError code: {response},\nDescription: {description},\n\naddress: {address},\ncoin:{coin},\nis_long_short: {position_side},\ntime: {self.get_current_time()},\ntransaction_quantity: {transaction_quantity},\ntransaction_amount: {transaction_amount}\n,\nour_total_hold:{our_total_hold},\navg_coin_price:{avg_coin_price}\n\n\n\n{content_prints}"
                self.send_message("ALERT", content)




#---Liquidation----------
    def ultimate_liquidateTrade(self,client, address, coin, position_side):

        print("Time:", self.get_current_time())
        # Symbol value
        symbol = coin + "USDT"

        # Setting takeprofit also for liquia=dated trades
        def liquidateTrade(client, address, coin, position_side):

        #---------------------------
            weighted_score_ratio = traders_list['Ranking_Score'][traders_list['account'] == address].iloc[0] / traders_list['Ranking_Score'].sum()
            leads_max_volume = traders_list['max_volume'][traders_list['account'] == address].iloc[0]

            try:                                                                                                                  #  added new check
                exchange_information = client.futures_exchange_info()
                symbol_info = next((s for s in exchange_information['symbols'] if s['symbol'] == symbol), None)  # corrected line
                if symbol_info:
                    # Precision for the quantity
                    quantity_precision = next((f['stepSize'] for f in symbol_info['filters'] if f['filterType'] == 'MARKET_LOT_SIZE'), None)
                    # Precision for the price in dollar
                    price_precision =  next((f['tickSize'] for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER'), None)
                    # Minimum notional value (minimum dollars)
                    min_notional = float(next((f['notional'] for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None))
                    # Get integer value of precision
                    quantity_precision_integer = 0 if '.' not in str(quantity_precision) else len(
                        str(quantity_precision).split('.')[1].rstrip('0')) if str(quantity_precision) else None
                    price_precision_integer = 0 if '.' not in str(price_precision) else len(
                        str(price_precision).split('.')[1].rstrip('0')) if str(price_precision) else None
                    
                    quantity_precision_integer = int(quantity_precision_integer)
                    price_precision_integer = int(price_precision_integer)
                    
                    try:                                                                                             #  added new check
                        ticker = client.futures_symbol_ticker(symbol=symbol)
                        price_on_bin = float(ticker['price'])
                        print(f"Current market price of {symbol}: {price_on_bin}")
                    except Exception as e:
                        print(f"Error occurred during coin {symbol} price fetching from Binance.\nException: {traceback.format_exc()}")
                        return 3001, f"Error occurred during coin {symbol} price fetching from Binance.\nException: {e}"
                    # Minimum quantity to buy
                    minimum_quantity_usdt = min_notional/price_on_bin
                    min_qty = self.round_up_to_ceil_with_precision(minimum_quantity_usdt, quantity_precision_integer)
                else:
                    print(f"Symbol {symbol} not found in exchange information.")
                    return 3002, f"Symbol {symbol} not found in exchange information."  # Error code and description , above we used 1005 and its same error check
            except Exception as e:
                print(f"Error occurred during coin info fetching from Binance.\nException: {traceback.format_exc()}")
                return 3003, f"Error occurred during coin info fetching from Binance.\nException: {e}"


            # Rechecking old stop loss and filling df if executed
            response_from_old_stop_loss = self.check_old_stop_loss(client, trading_data_df, address, symbol, position_side) 
            print('Trying to check old stop loss status before moving on.')
            if response_from_old_stop_loss == False:
                print(f"Exception happened while check_old_stop_loss.")
                return False, f"Exception happened while check_old_stop_loss."
            
            # Getting Data from leads last row in this position
            leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)

            # Check if we have any hold for that trader or not
            if our_total_hold == 0:
                print("No holding for the lead to close in liquidation trade.")
                return True, "No holding for the lead to close in liquidation trade."
            
            quantity_to_close = our_total_hold
            print("our_total_hold: ",our_total_hold)
            print("avg_coin_price: ",avg_coin_price)
            
            # Fetching open_side value i.e buy or sell
            open_side, close_side = self.sideAndCounterSideForBinance(position_side)

            print("Canceling older stop_loss.")

            print(f"Old stoploss orderId: {stop_loss_order_id}")
            print('Trying to cancel old stop loss')
            for i in range(number_of_try):  
                try:
                    cancel_older_stoploss = client.futures_cancel_order(symbol=symbol, orderId=stop_loss_order_id)

                    canceled_order_orderId = str(cancel_older_stoploss['orderId']) # Assigning orderid in string format.
                    print("Older stoploss cancelation order placed successfully.")
                    break

                except Exception as e: #Error when 3rd try is not successful
                    print("Error canceling older stoploss order:", e)
                    if i <= (number_of_try - 2): 
                        print(f"Retrying cancel_older_stoploss in {retry_time} seconds...(try no: {i}/{number_of_try})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Exception happened while canceling old stop_loss.\nException: {traceback.format_exc()}")
                        return 1011, f"Exception happened while canceling old stop_loss.\nException: {e}"
            time.sleep(retry_time)
            #Checking cancelation status n number of time
            for i in range(number_of_try): 
                try:                    
                    order_status_stop_loss = client.futures_get_order(   # check new
                        symbol=symbol,
                        orderId= canceled_order_orderId
                    )
                    if order_status_stop_loss['status'] == "CANCELED":
                        print(f"Stoploss order status is CANCELED. orderID: {cancel_older_stoploss['orderId']}")
                        break
                    else:
                        if i <= (number_of_try - 2):
                            print(f"Stoploss order cancelation status is NOT CANCELED. orderID: {cancel_older_stoploss['orderId']}")
                            print(f"Retrying checking order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Stoploss order cancelation status is NOT CANCELED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED).")
                            return 1010, f"Stoploss order cancelation status is NOT CANCELED after checking {number_of_try} times, exiting the trade(check the status now and close postion manually if status id CANCELED)."

                except Exception as e: #Error when 3rd try is not successful
                    print("Error checking cancelation order status:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while checking status of older stop_loss cancelation order.\nException: {traceback.format_exc()}")
                        return 1011, f"Error occurred while checking status of older stop_loss cancelation order.\nException: {e}"
                       

            print("Closing our_total_hold.")
            #Clsoing order market.
            for i in range(number_of_try):
                try:
                    market_order = client.futures_create_order(symbol=symbol, positionSide=position_side, side=close_side,
                                            type=client.FUTURE_ORDER_TYPE_MARKET, quantity=quantity_to_close)

                    market_orderId = str(market_order['orderId']) # Assigning orderid in string format.

                    current_trade_orderId = market_orderId

                    print("Market close trade order placed successfully. market_orderId: ", market_orderId)
                    break

                except Exception as e: #Error when 3rd try is not successful
                    print("Error placing order:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying placing market order in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while placing market close trade order.\nException: {traceback.format_exc()}")
                        return 1009, f"Error occurred while placing market close trade order.\nException: {e}"
            time.sleep(retry_time)
            # Trying to check market close trade order status n number of times.
            print("Checking market close trade order status if FILLED or NOT.")
            for i in range(number_of_try):
                try:
                    order_status = client.futures_get_order(
                        symbol=symbol,
                        orderId= market_orderId
                        )

                    if order_status['status'] == "FILLED":       # check new , earlier orderStatus SUCCESS was written, 'status': 'FILLED', or 'NEW'
                        print(f"Market close order status is FILLED, orderId: {order_status['orderId']}")
                        break
                    else:
                        if i <= (number_of_try - 2):
                            print(f"Market close order status is NOT FILLED. orderId: {order_status['orderId']}")
                            print(f"Retrying checking order status in {retry_time} seconds...({i})")
                            time.sleep(retry_time)
                            continue
                        else:
                            print(f"Market close order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close it manually if status id FILLED).")
                            return 1010, f"Market close order status is NOT FILLED after checking {number_of_try} times, exiting the trade(check the status now and close it manually if status id FILLED)."
                            
                except Exception as e: #Error when 3rd try is not successful
                    print("Error checking order status:", e)
                    if i <= (number_of_try - 2):
                        print(f"Retrying requesting order status in {retry_time} seconds...({i})")
                        time.sleep(retry_time)
                        continue
                    else:
                        print(f"Error occurred while checking status of market close trade order.\nException: {traceback.format_exc()}")
                        return 1011, f"Error occurred while checking status of market closeopen trade order.\nException: {e}"

            marketOrderQty, marketOrderPrice = float(order_status['executedQty']), float(order_status['avgPrice'])
            new_our_transaction_amount = marketOrderQty * marketOrderPrice
            print("marketOrderQty: ",marketOrderQty)
            print("marketOrderPrice: ",marketOrderPrice)
            # PNL
            y = 1 if position_side == "LONG" else -1
            PNL = marketOrderQty * (marketOrderPrice - avg_coin_price) * (y)                                         # check
            print(f"PNL: {PNL}")


            # Append new row in the Trading_df with all updated details details.
            self.add_to_trading_data_df(
                time= self.get_current_time(), 
                trade_order_id=market_orderId,
                address=address, 
                symbol=symbol, 
                is_long_short=position_side,
                trade_type="LIQUIDATED",
                leads_price=0,
                price=marketOrderPrice,
                weighted_score_ratio=weighted_score_ratio,
                leads_max_volume=leads_max_volume,
                leads_leverage=leads_leverage,
                leads_transaction_quantity=leads_total_hold,
                leads_transaction_amount=leads_total_investment,
                our_leverage=our_leverage,
                our_transaction_quantity=marketOrderQty,
                our_transaction_amount=new_our_transaction_amount,
                leads_total_hold=leads_total_hold,
                leads_total_investment=leads_total_investment,
                avg_leads_coin_price=avg_leads_coin_price,
                our_total_hold=0,
                our_total_investment=our_total_investment,
                avg_coin_price=avg_coin_price,
                total_hold_ratio=total_hold_ratio,
                stop_loss_price=0,
                stop_loss_order_id= None,
                is_stop_loss_executed=False,
                is_liquidated= True,
                take_profit_price=0,
                take_profit_order_id=None,
                PNL=PNL
            )
            
            # Return the code as True and error description as None if everything goes succesfully
            return True, None

        collector = Collector()
        collector.start_collecting()

        response, description = liquidateTrade(client, address, coin, position_side)

        collector.stop_collecting()
        content_prints = collector.content

        if response == True:
            pass
        else:
            # Getting Data from leads last row in this position
            leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)
            #Writing content for email
            content = f"Position liquidated and some error occoured.\nError code: {response},\nDescription: {description},\n\naddress: {address},\ncoin:{coin},\nis_long_short: {position_side},\ntime: {self.get_current_time()},\nour_total_hold: {our_total_hold},\n,avg_coin_price: {avg_coin_price}\n\n\n{content_prints}"
            self.send_message("ALERT", content)




#---Others----------
    # Function to add a dictionary to the list with a timestamp
    def add_to_ban_list(self, address, symbol, position_side, market_orderId, current_market_OrderQty, current_market_OrderPrice, new_our_total_hold, new_avg_coin_price):
        trade_info = {
            "address": address,
            "symbol": symbol,
            "is_long_short": position_side,
            "timestamp": self.get_current_time()  # Add current timestamp
        }

        ban_positions_info_list.append(trade_info)
        print("Position successfully added to Ban list.")
        print(f"Position banned for (hours= {ban_time_hours})")
        try:
            message_trade =  f"{dex_name}: Banned Position Update (Banned at {self.get_current_time()}, for the next {ban_time_hours} hours)"
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = ", ".join(receiver_email)
            message["Subject"] = message_trade

            # Get the current time in IST
            now = self.get_current_time()

            rows = [
                    ["Time", self.get_current_time()],
                    ["ban_time_hours", ban_time_hours],
                    ["address", address],
                    ["symbol", symbol],
                    ["position_side", position_side],
                    ["current_market_OrderQty", current_market_OrderQty],
                    ["current_market_OrderPrice", current_market_OrderPrice],
                    ["new_our_total_hold", new_our_total_hold],
                    ["new_avg_coin_price", new_avg_coin_price],
                    ["DEX", dex_name],
                ]
            
            self.add_to_trading_data_df(
                    time= self.get_current_time(),
                    trade_order_id=market_orderId,
                    address=address,
                    symbol=symbol,
                    is_long_short=position_side,
                    trade_type='BANNED',
                    leads_price=0,
                    price=current_market_OrderPrice,
                    weighted_score_ratio=0,
                    leads_max_volume=0,
                    leads_leverage=0,
                    leads_transaction_quantity=0,
                    leads_transaction_amount=0,
                    our_leverage=our_leverage,
                    our_transaction_quantity=current_market_OrderQty,
                    our_transaction_amount=current_market_OrderPrice*current_market_OrderQty,
                    leads_total_hold=0,
                    leads_total_investment=0,
                    avg_leads_coin_price=0,
                    our_total_hold=new_our_total_hold,
                    our_total_investment=new_our_total_hold*new_avg_coin_price,
                    avg_coin_price=new_avg_coin_price,
                    total_hold_ratio=0,
                    stop_loss_price=0,
                    stop_loss_order_id=None,
                    is_stop_loss_executed=False,
                    is_liquidated=False,
                    take_profit_price=0,
                    take_profit_order_id=None,
                    PNL=0
                )
            

            table_html = self.create_table_html(rows)
            message.attach(MIMEText(self.generate_html_with_date(), "html")) 
            # Attach table as HTML to the email
            message.attach(MIMEText(table_html, "html"))     

            print("\n**ban_positions_info_list: \n",ban_positions_info_list, "\n")

            email_server = smtplib.SMTP("smtp.gmail.com", 587)
            email_server.starttls()
            email_server.login(sender_email, email_password)
            email_server.sendmail(sender_email, receiver_email, message.as_string())
            
        except Exception as e:
            print(f"Error occurred while constructing or sending the email for banned position update. \nException: {traceback.format_exc()}")


    # Fucntion to check if position is banned
    def is_position_banned(self, address, symbol, position_side):
        for trade_info in ban_positions_info_list:
            if (trade_info["address"] == address and
                    trade_info["symbol"] == symbol and
                    trade_info["is_long_short"] == position_side):
                # Check if time is more than 48 hours ago
                trade_time_str = trade_info.get("timestamp")
                if trade_time_str:
                    try:
                        # Parse the timestamp string to datetime using the specified format
                        trade_time = datetime.strptime(trade_time_str, "%H:%M:%S %d %B %Y")
                        if datetime.now() - trade_time > timedelta(hours=ban_time_hours):
                            # Remove the trade info from the list
                            ban_positions_info_list.remove(trade_info)
                            return False  # Trade info found but expired
                    except ValueError:
                        print(f"Invalid timestamp format in ban_positions_info_list: {trade_time_str}")
                        return False  # Invalid timestamp format
                return True  # Trade info found and within 48 hours
        return False  # Trade info not found


    # Returns total hold and other useful data for email when error happens. 
    def error_return_latest_data(self, address, symbol, position_side, current_trade_orderId, client):
        
        current_market_OrderQty = 0
        current_market_OrderPrice = 0
        market_order_status = None
        try:
            market_order_status = client.futures_get_order(symbol=symbol, orderId=current_trade_orderId)
            current_market_OrderQty, current_market_OrderPrice = float(market_order_status['executedQty']), float(market_order_status['avgPrice'])
        except:
            print(f"Exception happened while error_return_latest_data.\nException: {traceback.format_exc()}")

        print(f"market_order_status of the trade taken before error:\n{market_order_status}")

        # Now check the last row through below function & fetch last row values from Trading_df about the current position
        leads_total_hold, leads_total_investment, avg_leads_coin_price, leads_leverage, our_total_hold, our_total_investment, avg_coin_price, total_hold_ratio, stop_loss_order_id, stop_loss_price, was_last_row_present = self.get_last_row_of_trader_in_trading_data_df(trading_data_df, address, symbol, position_side)

        # Calculating new total holds & avg coin price
        new_our_total_hold = float(current_market_OrderQty) + float(our_total_hold) * 1
        if float(new_our_total_hold) == 0:
            new_avg_coin_price = 0
        else:
            new_avg_coin_price = (float(current_market_OrderQty) * float(current_market_OrderPrice) + float(avg_coin_price) * float(our_total_hold)) / float(new_our_total_hold)

        return current_market_OrderQty, current_market_OrderPrice, new_our_total_hold, new_avg_coin_price, market_order_status






order_type_map = {
    0: 'Market_Swap',
    1: 'Limit_Swap',
    2: 'Market_Increase',
    3: 'Limit_Increase',
    4: 'Market_Decrease',
    5: 'Limit_Decrease',
    6: 'Stop_Loss_Decrease',
    7: 'Liquidation'
}



markets = {
    # market_token_address : (coin_pair, coin_pair2, index_token_decimals, index_token_decimals_minus_30, long_token_decimals, short_token_decimals)
    'BTCUSDT': ['BTC/USD', 'BTC-USDC', 8, 22, 8, 6],
    'ETHUSDT': ['ETH/USD', 'WETH-USDC', 18, 12, 18, 6],
    'DOGEUSDT': ['DOGE/USD', 'WETH-USDC', 8, 22, 18, 6],
    'SOLUSDT': ['SOL/USD', 'SOL-USDC', 9, 21, 9, 6],
    'LTCUSDT': ['LTC/USD', 'WETH-USDC', 8, 22, 18, 6],
    'UNIUSDT': ['UNI/USD', 'UNI-USDC', 18, 12, 18, 6],
    'LINKUSDT': ['LINK/USD', 'LINK-USDC', 18, 12, 18, 6],
    'ARBUSDT': ['ARB/USD', 'ARB-USDC', 18, 12, 18, 6],
    '0x9c2433dfd71096c435be9465220bb2b189375ea7': ['SWAP-ONLY', 'USDC-USDC.e', 18, 12, 6, 6],
    '0xb686bcb112660343e6d15bdb65297e110c8311c4': ['SWAP-ONLY', 'USDC-USDT', 18, 12, 6, 6],
    '0xe2fedb9e6139a182b98e7c2688ccfa3e9a53c665': ['SWAP-ONLY', 'USDC-DAI', 18, 12, 6, 18],
    'XRPUSDT': ['XRP/USD', 'WETH-USDC', 6, 24, 18, 6],
    'BNBUSDT': ['BNB/USD', 'BNB-USDC', 18, 12, 18, 6],
    'AAVEUSDT': ['AAVE/USD', 'AAVE-USDC', 18, 12, 18, 6],
    'ATOMUSDT': ['ATOM/USD', 'WETH-USDC', 6, 24, 18, 6],
    'NEARUSDT': ['NEAR/USD', 'WETH-USDC', 24, 6, 18, 6],
    'AVAXUSDT': ['AVAX/USD', 'AVAX-USDC', 18, 12, 18, 6],
    'OPUSDT': ['OP/USD', 'OP-USDC', 18, 12, 18, 6],
    'BTCUSDT': ['BTC/USD', 'BTC', 8, 22, 8, 8],
    'ETHUSDT': ['ETH/USD', 'WETH', 18, 12, 18, 18],
    'GMXUSDT': ['GMX/USD', 'GMX-USDC', 18, 12, 18, 6],
    # Follow this URL to get the details of all market tokens "https://github.com/gmx-io/gmx-interface/blob/master/src/domain/synthetics/__tests__/stats/marketsInfoDataToIndexTokensStats.data.json"
}


collaterals = {
    # This is to consider collateral token decimals for getting correct collateral value.
    '0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f': ['BTC', 8],
    '0x82af49447d8a07e3bd95bd0d56f35241523fbab1': ['WETH', 18],
    '0x2bcc6d6cdbbdc0a4071e48bb3b969b06b3330c07': ['SOL', 9],
    '0xfa7f8980b0f1e64a2062791cc3b0871572f1f7f0': ['UNI', 18],
    '0xf97f4df75117a78c1a5a0dbb814af92458539fb4': ['LINK', 18],
    '0x912ce59144191c1204e64559fe8253a0e49e6548': ['ARB', 18],
    '0xaf88d065e77c8cc2239327c5edb3a432268e5831': ['USDC', 6],
    '0xa9004a5421372e1d83fb1f85b0fc986c912f91f3': ['BNB', 18],
    '0xba5ddd1f9d7f570dc94a51479a000e3bce967196': ['AAVE', 18],
    '0x565609faf65b92f7be02468acf86f8979423e514': ['AVAX', 18],
    '0xac800fd6159c2a2cb8fc31ef74621eb430287a5a': ['OP', 18],
    '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8': ['USDC.E', 6],
    '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9': ['USDT', 6],
    '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1': ['DAI', 18],
    '0xc4da4c24fd591125c3f47b340b6f4f76111883d8': ['DOGE', 8],
    '0xb46a094bc4b0adbd801e14b9db95e05e28962764': ['LTC', 8],
    '0xc14e065b0067de91534e032868f5ac6ecf2c6868': ['XRP', 6],
    '0x7d7f1765acbaf847b9a1f7137fe8ed4931fbfeba': ['ATOM', 6],
    '0x1ff7f3efbb9481cbd7db4f932cbcd4467144237c': ['NEAR', 24],
    '0x47904963fc8b2340414262125af798b9655e58cd': ['BTC', 8],
    '0xfc5a1a6eb076a2c7ad06ed22c90d7e710e35ad0a': ['GMX', 18]
}


# Main class for taking trades and running loop
class livePositionExtractiontest:  # Runs the loop function to return information on a trader, if any of the 3 events are run.

    def __init__(self, proxy_contract, client, traders_list):
        self.client = client
        self.traders_list = traders_list
        self.proxy_contract = proxy_contract
        self.trade = Trading_Things()

        # Initialize Web3 client for backward compatibility (though it won't be used for data fetching)
        self.w3 = Web3(Web3.HTTPProvider(alchemy_url))
        print(self.w3.is_connected())

        self.proxy_address = Web3.to_checksum_address(proxy_contract)
        self.contract = self.w3.eth.contract(address=self.proxy_address, abi=ABI)

    def fetch_live_data(self):
        """
        Fetch live data from Scraper Bot's Google Sheets.
        """
        credentials_file = {
#
        }

        credentials = Credentials.from_service_account_info(credentials_file)
        service = build('sheets', 'v4', credentials=credentials)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SHEET_ID, range=SHEET_NAME).execute()
        rows = result.get('values', [])
        return rows


    def loop(self):
        global trading_data_df_length_stored  # Access the global variable
    
        while True:
            try:
                # Fetch live data from Google Sheets
                data = self.fetch_live_data()  # This function retrieves data from Google Sheets
            
                for row in data[1:]:  # Skip the header row
                    try:
                        # Extract values from the row as per column order matching the original function
                        id_value, event_name, account, market_value, side, event, \
                        collateral_value, collateral_amount_raw, \
                        size_in_usd_raw, trigger_price_raw, \
                        execution_price_raw, pnl_used_raw, base_pnl_used_raw, \
                        min_output_amount_raw, execution_amount_out_raw, \
                        price_impact_used_raw, price_impact_diff_used_raw, \
                        position_fee_amount_raw, borrowing_fee_amount_raw, \
                        funding_fee_amount_raw, collateral_token_price_max_raw, \
                        collateral_token_price_min_raw, index_token_price_min_raw, \
                        index_token_price_max_raw, transaction_timestamp, \
                        transaction_hash = row

                        address = account.lower()

                        # Matching the original function's calculations exactly
                        execution_price = float(execution_price_raw)
                        size_in_usd = int(size_in_usd_raw) / 1e30
                        size_in_tokens_raw=float(float(size_in_usd_raw)/float(execution_price_raw))
                        size_in_tokens = float(size_in_tokens_raw) / 10**(markets[market_value][2])
                        asset_price = execution_price / 10**(markets[market_value][3])
                        
                        # Collateral amount calculation matching the original function
                        if collateral_value == "USDC":
                            collateral_amount = float(collateral_amount_raw) / 10**(collaterals[collateral_value][1])
                        else: 
                            collateral_token_price_max = float(row[21])  # Assuming this is the collateral token price max
                            collateral_token_price_min = float(row[22])  # Assuming this is the collateral token price min
                            collateral_amount = (float(collateral_amount_raw) * ((collateral_token_price_max + collateral_token_price_min) / 2)) / 10**30

                        transaction_amount = float(size_in_usd_raw) / 1e30
                        print(type(transaction_amount))
                        print(type(size_in_usd_raw))
                        # Ensure both size_in_usd_raw and execution_price_raw are floats
                        try:
                            size_in_usd = float(size_in_usd_raw)  # Convert to float explicitly
                            execution_price = float(execution_price_raw)  # Convert to float explicitly

                            # Compute transaction amount and quantity
                            transaction_amount = size_in_usd / 1e30
                            transaction_quantity = (size_in_usd / execution_price) / 10 ** (markets[market_value][2])
                        except ValueError as e:
                            logging.error(
                                f"Conversion error for size_in_usd: {size_in_usd_raw}, execution_price: {execution_price_raw}. Error: {e}")
                            continue  # Skip this row if there's a problem
                        print(type(transaction_amount))
                        print(type(size_in_usd_raw))
                        transaction_quantity = float(size_in_usd_raw / execution_price_raw) / 10 ** (
                        markets[market_value][2])

                        # Additional logic for zero values
                        if size_in_tokens == 0 or collateral_amount == 0 or size_in_usd == 0:
                            if size_in_tokens == 0 and collateral_amount == 0 and size_in_usd == 0 and event_name.lower() == "positiondecrease":
                                print(f"*size_in_tokens={size_in_tokens} & collateral_amount={collateral_amount} & size_in_usd={size_in_usd}, i.e position completely closed by the trader, hence, we are also CLOSING the trade 100%*")
                                print("Passing new_leads_leverage = our_leverage as leverage calculation for the trader's position is no more possible.")
                                new_leads_leverage = round((transaction_amount/collateral_amount), 1)
                                if new_leads_leverage == 0:
                                    new_leads_leverage = our_leverage
                            else:
                                print(f"*size_in_tokens={size_in_tokens} OR collateral_amount={collateral_amount} OR size_in_usd={size_in_usd}, i.e this trade is abnormal, rejecting trade (event_type: {event_name}.")
                                continue
                        else:
                            new_leads_leverage = round((size_in_usd/collateral_amount), 1)

                        # Check if the trader is in the list
                        if address in self.traders_list['account'].values:
                            print(f"\n\nProcessing trade for {address}, market: {market_value}")

                            # Market and collateral validation
                            if market_value in markets:
                                market = markets[market_value]
                                coin_pair = market[0]
                                coin_pair2 = market[1]
                                coin = coin_pair.split('/')[0]
                            else:
                                print(f"UNKNOWN Market Token: {market_value}")
                                continue

                            if collateral_value in collaterals:
                                collateral = collaterals[collateral_value]
                                collateral_token = collateral[0]
                            else:
                                print(f"UNKNOWN Collateral Token: {collateral_value}")
                                continue

                            # Position side and event type matching original function
                            position_side = side
                            event = "OPEN" if event_name.lower() == "positionincrease" else "CLOSE"

                            # Order type matching
                            order_type_value = int(row[12])  # Assuming this is the order type value column
                            orderType = order_type_map.get(order_type_value, "UNKNOWN")

                            if orderType == "UNKNOWN":
                                print(f"UNKNOWN orderType={order_type_value} appeared. Rejecting trade.")
                                continue

                            # Stop signal check (matching original function)
                            try:
                                if os.path.exists(stop_signal_path):
                                    with open(stop_signal_path, "r") as file:
                                        stop_signal = file.read().strip()
                                else:
                                    stop_signal = ""
                            except:
                                stop_signal = ""

                            # Trade processing logic matching original function
                            if event_name.lower() == "positionincrease":
                                if stop_signal != "STOP":
                                    # Symbol for position banning check
                                    symbol = coin + "USDT"
                                    
                                    # Checking if banned
                                    if self.trade.is_position_banned(address, symbol, position_side):
                                        print("--Banned position, rejecting further processing--")
                                        continue

                                    # Checking if the parameters are valid
                                    if transaction_quantity != 0:
                                        try:
                                            self.trade.ultimate_openTrade(
                                                self.client, 
                                                self.traders_list, 
                                                address, 
                                                coin, 
                                                position_side, 
                                                asset_price, 
                                                transaction_amount, 
                                                transaction_quantity, 
                                                new_leads_leverage
                                            )
                                        except Exception as e: 
                                            print(f"Exception happened while OPEN trade.\nException: {traceback.format_exc()}\n\n")
                                            content = f"Exception happened while OPEN trade.\n\nPosition Side: {position_side}\nAddress: {address}\nCoin: {coin}\nAsset Price: {asset_price}\nTransaction Amount: {transaction_amount}\nTransaction Quantity: {transaction_quantity}\nNew Leads Leverage: {new_leads_leverage}\nException: {traceback.format_exc()}\n\n"
                                            self.trade.send_message("ALERT", content)
                                            continue
                                    else:
                                        print("Trade transaction_quantity = 0, rejecting trade.")
                                        continue
                                else:
                                    print("\n\n\n\n\n---------------** STOP ** Signal Received. Rejecting: OPEN TRADES.---------------\n\n\n\n\n")

                            elif event_name.lower() == "positiondecrease" and order_type_value != 7:
                                # Symbol for position banning check
                                symbol = coin + "USDT"
                                
                                # Checking if banned
                                if self.trade.is_position_banned(address, symbol, position_side):
                                    print("--Banned position, rejecting further processing--")
                                    continue

                                # Checking if the parameters are valid
                                if transaction_quantity != 0:
                                    try:
                                        self.trade.ultimate_closeTrade(
                                            self.client, 
                                            self.traders_list, 
                                            address, 
                                            coin, 
                                            position_side, 
                                            asset_price, 
                                            transaction_amount, 
                                            transaction_quantity, 
                                            new_leads_leverage
                                        )
                                    except Exception as e: 
                                        print(f"Exception happened while CLOSE trade.\nException: {traceback.format_exc()}\n\n")
                                        content = f"Exception happened while CLOSE trade.\n\nPosition Side: {position_side}\nAddress: {address}\nCoin: {coin}\nAsset Price: {asset_price}\nTransaction Amount: {transaction_amount}\nTransaction Quantity: {transaction_quantity}\nNew Leads Leverage: {new_leads_leverage}\nException: {traceback.format_exc()}\n\n"
                                        self.trade.send_message("ALERT", content)
                                        continue
                                else:
                                    print("Trade transaction_quantity = 0, rejecting trade.")
                                    continue

                            elif event_name.lower() == "positiondecrease" and order_type_value == 7:
                                # Symbol for position banning check
                                symbol = coin + "USDT"
                                
                                # Checking if banned
                                if self.trade.is_position_banned(address, symbol, position_side):
                                    print("--Banned position, rejecting further processing--")
                                    continue

                                try:
                                    self.trade.ultimate_liquidateTrade(
                                        self.client, 
                                        address, 
                                        coin, 
                                        position_side
                                    ) 
                                except Exception as e: 
                                    print(f"Exception happened while LIQUIDATE trade.\nException: {traceback.format_exc()}\n\n")
                                    content = f"Exception happened while LIQUIDATE trade.\n\nPosition Side: {position_side}\nAddress: {address}\nCoin: {coin}\nException: {traceback.format_exc()}\n\n"
                                    self.trade.send_message("ALERT", content)
                                    continue

                            else:
                                print("----UNKNOWN event_name or condition occurred in GMXV2, so rejecting the trade.----")
                                continue

                    except Exception as e:
                        print(f"Error processing row: {row}. Exception: {traceback.format_exc()}")

                # Check for changes in trading data and update accordingly
                current_length = len(trading_data_df)
                if current_length != trading_data_df_length_stored:
                    trading_data_df_length_stored = current_length
                    self.trade.get_and_upload_open_positions_to_sheets()
                    print(f"Executed get_and_upload_open_positions_to_sheets.")

                # Check summary email trigger
                global last_email_sent_date
                now_str = self.trade.get_current_time()
                now = datetime.strptime(now_str, "%H:%M:%S %d %B %Y")
                if now.hour == summary_sending_hour and (last_email_sent_date is None or last_email_sent_date < now.date()):
                    self.trade.get_summary_and_send_email()
                
                time.sleep(0.5)  #This is to decrease the alchemy url usage
        
            except Exception as e:
                print(f"Error in loop: {traceback.format_exc()}")



#Testnet API
binance_api = "#"
binance_secret = "#"


dots = 0
# Initialize the Binance client instance
while True:
    try:
        client = Client(binance_api, binance_secret, testnet=True)
        print("\nConnected")
        break
    except:
        message = f"Not Connected{'.' * dots}"
        print(f"\r{message:<20}", end="", flush=True)  # Add padding to ensure overwriting
        # Increase the number of dots, resetting after 3
        dots = (dots + 1) % 4


#Open a file for writing both stdout and stderr
log_filename = f"{DEX[0]}_log.txt"
log_file = open(log_filename, 'a', buffering=1)
sys.stdout = sys.stderr = log_file

xyz = Trading_Things()
try:
    # Main code
    print(f"\n\n\n\n--------------------------------------{DEX[0]}-Program Starting Time: {xyz.get_current_time()}--------------------------------------\n")

    livePositionExtractiontest(proxy_contract, client, traders_list).loop()

except Exception as e:
    # Capture any unhandled exceptions and write to log
    print(f"\n\n\n----Exception occurred outside the loop at {xyz.get_current_time()}----\n")
    traceback.print_exc()

    content = f"Exception occurred outside the loop in {DEX[0]} at {xyz.get_current_time()}\nException: {traceback.format_exc()}"
    xyz.send_message("CRASHED", content)

finally:
    # Close the log file
    log_file.flush()
    log_file.close()
