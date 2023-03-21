from FIutils import *
import keys as k
import pickle
# this is to cache data for testing
from os.path import exists


if exists('cache.data'):
    with open('cache.data', 'rb') as cacheFile:
        stocks = pickle.load(cacheFile)
    print("### Loaded cache.data ###")
else:
    # create a file called 'keys.py'
    # define av_apikey = 'your-api-key'
    # ensure it is in the working directory
    AVapiKey = k.apikey
    totalCallCount = 0
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

    # getsymbols returns a dataframe of ~11k stocks and etfs
    stockDF = getsymbols(AVapiKey)
    # this filters the stocks and then gets a list of the symbols
    stocksymbolslist = stockDF[stockDF['assetType'] == 'Stock']['symbol'].tolist()
    stocks = []
    for str in stocksymbolslist:
        stocks.append(Stock(str))

    '''teststock = Stock('F')
    teststock.fetch_data(AVapiKey)
    teststock.analyze(sizeLowerBound, sizeUpperBound)
    teststock.printInfo()
    for key in teststock.fd.keys():
        print(f"{key}: {teststock.fd[key]}")'''

    print(f"Getting data on {len(stocks)+1} stocks.")
    # basic for loop that will run our analysis
    count = 0
    for obj in stocks:
        print(f"[{count+1}/{len(stocks)+1}]: {obj.symbol}\tcall #: {totalCallCount}")
        count += 1
        obj.fetch_data(AVapiKey)
        obj.analyze(sizeLowerBound, sizeUpperBound)
        # obj.printInfo()

# this is to cache data for local testing
with open('cache.data', 'wb') as cacheFile:
    pickle.dump(stocks, cacheFile)
    print("stocks list successfully cached in cache.data")
