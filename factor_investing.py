from utils import *
import time as time
# create a file called 'keys.py'
# define av_apikey = 'your-api-key'
# ensure it is in the working directory
import keys as k
import pickle
from os.path import exists
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from datetime import datetime

size_param = 'micro-cap'
companySizes = {
    "nano-cap" : (0, 50_000_000),
    "micro-cap" : (50_000_000, 300_000_000),
    "small-cap" : (300_000_000, 2_000_000_000),
    "mid-cap" : (2_000_000_000, 10_000_000_000),
    "large-cap" : (10_000_000_000, 200_000_000_000),
    "mega-cap" : (200_000_000_000, float('inf')) 
}
sizeLowerBound, sizeUpperBound = companySizes[size_param]
timeWeek = 60 * 60 * 24 * 7

subset = [Stock('F')]
portfolio = []

def submit_sell_order(alpaca_api, stock):
    market_order_data = MarketOrderRequest(symbol=stock.symbol, qty=stock.qty, side=OrderSide.SELL, time_in_force=TimeInForce.GTC)
    market_order = alpaca_api.submit_order(market_order_data)

def submit_buy_order(alpaca_api, stock, qty):
    market_order_data = MarketOrderRequest(symbol=stock.symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.GTC)
    market_order = alpaca_api.submit_order(market_order_data)

def get_cash_balance(alpaca_api):
    account = alpaca_api.get_account
    return float(account.cash)

def sync_portfolio(alpaca_api):
    positions = alpaca_api.get_all_positions()
    synced_portfolio = []

    for position in positions:
        stock = Stock(position.symbol)
        stock.qty = int(position.qty)
        stock.fetchData(k.av_apikey)
        stock.analyze(sizeLowerBound, sizeUpperBound)
        synced_portfolio.append(stock)
    with open("portfolio.data", "wb") as portfolioFile:
            pickle.dump(synced_portfolio, portfolioFile)
    return synced_portfolio

'''def analyzePortfolio(portfolio):
    print("Getting data and analyzing current portfolio")
    for obj in portfolio:
        obj.fetchData(k.av_apikey)
        obj.analyze(sizeLowerBound, sizeUpperBound)'''

def identifyJunk(portfolio, topTickers):
    for obj in portfolio:
        condition = obj.symbol in topTickers
        if not condition:
            obj.junk = True
    return

def identifyGold(subset, n):
    tickerList = []
    qualified = []
    for obj in subset:
        condition = obj.value and obj.sizeBool and obj.momentum_3m and obj.momentum_6m
        if condition:
            qualified.append(obj)
    qualified.sort(key = lambda x: x.momentum_1yr, reverse=True)
    n = min(n, len(qualified))
    for index in range(n):
        tickerList.append(qualified[index].symbol)
        subset[index].gold = True
    return tickerList

def printPlannedSell(portfolio):
    for obj in portfolio:
        if obj.junk:
            print("Selling: ", obj.symb, "Qty: ", obj.qty)
            obj.printInfo()

def sellJunk(portfolio):
    print("\n\nSelling Junk")
    for obj in portfolio:
        if obj.junk:
            submit_sell_order(alpacaTradeAPI, obj)
            portfolio.remove(obj)
    return

def printPlannedBuy(subset, alpaca_api):
    cashBalance = get_cash_balance(alpaca_api)
    amountPerStock = cashBalance / numberAssets
    for obj in subset:
        if obj.gold:
            currPrice = float(obj.tsda['adjusted_close'].iloc[-1])
            qty2buy = int(amountPerStock / currPrice)
            print("Buying: ", obj.symbol, "Qty: ", qty2buy)
            obj.printInfo()

def buyGold(portfolio, subset, alpaca_api):
    print("\n\nBuying Gold")
    cashBalance = get_cash_balance(alpaca_api)
    amountPerStock = cashBalance / numberAssets
    for obj in subset:
        if obj.gold:
            currPrice = float(obj.tsda['adjusted_close'].iloc[-1])
            qty2buy = int(amountPerStock / currPrice)
            submit_buy_order(alpaca_api, obj, qty2buy)
            obj.gold = False
            portfolio.append(obj)
    return

def updateNextStock(subset):
    subset.sort(key = lambda x: x.time)
    subset[0].fetchData(k.av_apikey)
    subset[0].analyse(sizeLowerBound, sizeUpperBound)
    filename = f"stockDataCache/{subset[0].symbol}.data"
    with open(filename, "wb") as file:
        pickle.dump(file, subset[0])

def loadLocalStockData(subset):
    for obj in subset:
        filename = f"stockDataCache/{obj.symbol}.data"
        if exists(filename):
            with open(filename, "rb") as file:
                obj = pickle.load(filename)
                print(f"Loaded stock {obj.symbol} from cache")

# when we get to the 2 week time, run the analysis on the portfolio
# identify which stocks we should sell
# identify which we should buy from the stocks list
# sell and buy
# void loop:
# make calls on a stock, check if we are at two weeks
# if we are -> check position -> write data
# if we aren't -> continue
if exists("time.data"):
    with open("time.data", "rb") as timeFile:
        portfolioResetTime = pickle.load(timeFile)
else:
    portfolioResetTime = time.time()
    with open("time.data", "wb") as timeFile:
        pickle.dump(portfolioResetTime, timeFile)
numberAssets = 15
alpacaTradeAPI = TradingClient(k.alpaca_apikey, k.alpaca_secret, paper=True)
portfolio = sync_portfolio(alpacaTradeAPI)
loadLocalStockData(subset)
while True:
    currTime = time.time()
    if (currTime - portfolioResetTime) > 2 * timeWeek:
        portfolio = sync_portfolio(alpacaTradeAPI)
        topTickers = identifyGold(subset, numberAssets)
        if len(topTickers) != numberAssets:
            print(f"Could not identify {numberAssets} good stocks.")
            print(f"{len(topTickers)} stocks Qualified.")
        else:
            identifyJunk(portfolio, topTickers)
            printPlannedSell(portfolio)
            sellJunk(portfolio)
            printPlannedBuy(subset, alpacaTradeAPI)
            buyGold(portfolio, subset, alpacaTradeAPI)
        with open("time.data", "wb") as timeFile:
            pickle.dump(portfolioResetTime, timeFile)
    else:
        updateNextStock(subset)
        
    




