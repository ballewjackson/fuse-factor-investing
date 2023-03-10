from utils import *
import keys as k

# create a file called 'keys.py'
# define apikey = 'your-api-key'
# ensure it is in the working directory
AVapiKey = k.apikey

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

# basic for loop that will run our analysis
for obj in stocks:
    obj.fetch_data(AVapiKey)
    obj.analyze(sizeLowerBound, sizeUpperBound)
    obj.printInfo()
