import requests
import pandas as pd
import io as io
import json
import time

# Declaring variables for cutoffs and API requests
apikey = '39GO982RGG1GMTOV'
# outputStyles are compact and full
# these options only apply to tsda
outputStyle = 'full'
dataType = 'csv'

# what might be the best way to do profiles/factors
# like how should we go about changing the profile and factors
# one option is to create a dict and store a bool for each factor
# then you can just toggle which factors you want manually
# and analysis only runs on the ones toggled true
# sort/search operates on whatev er we define to be the search/sort criteria
# another option is a dict of premade profiles

size_param = 'micro-cap'
# this dictionary could allow us to implement easy multiSize analysis in the future
companySize = {
    "nano-cap" : (0, 50_000_000),
    "micro-cap" : (50_000_000, 300_000_000),
    "small-cap" : (300_000_000, 2_000_000_000),
    "mid-cap" : (2_000_000_000, 10_000_000_000),
    "large-cap" : (10_000_000_000, 200_000_000_000),
    "mega-cap" : (200_000_000_000, float('inf')) 
}
# usage: sizeLowerBound, sizeUpperBound = companySize[<str_company_size>]

# these are the sizes for "MicroCap" classification
sizeLowerBound = 50_000_000
sizeUpperBound = 300_000_000

callcount = 0
start_time=time.time()
def makeAPIcall(url):
    global callcount, start_time
    print("In call manager. Count:", callcount, "\tDeltatime:", time.time() - start_time)
    if callcount >= 4:
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            print("In sleep. Sleeping for:", 60-elapsed_time)
            time.sleep(60 - elapsed_time)
        callcount = 0
        start_time = time.time()

    # Make the API call and increment the counter
    response = requests.get(url)
    callcount += 1
    return response

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.value = False
        self.momentum_3m = False
        self.momentum_6m = False
        self.momentum_1yr = 0
        self.size = 0
        self.sizeBool = False
        # self.tsda for time_series_daily_adjusted; it is a dataframe
        self.tsda = None
        # self.fd will be a dictionary produced via json; fd for 'fundamental data'
        self.fd = {}
        # self.sector is a flag that we set automatically for the sector of the stock
        # would allow us to weight or adjust per sector
        self.sector = ""
    
    def printInfo(self):
        print(f"{self.fd['Name']}: {self.symbol}  {self.sector}  Size: {self.size}")
        print(f"Value: {self.value}\t3M Momentum: {self.momentum_3m}")
        print(f"6M Momentum: {self.momentum_6m}\t1YR Momentum: {self.momentum_1yr}")

    def fetch_data(self):
        ticker = self.symbol
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize={outputStyle}&datatype={dataType}&apikey={apikey}"
        response = makeAPIcall(url)
        #print(response.content)
        if response.status_code == 200:
            response_text = response.content.decode('utf-8')
            self.tsda = pd.read_csv(io.StringIO(response_text))
        else:
            print(f"Error fetching data for ticker {ticker}: {response.status_code}")

        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&datatype={dataType}&apikey={apikey}"
        response = makeAPIcall(url)
        if response.status_code == 200:
            response_text = response.content.decode('utf-8')
            self.fd = json.loads(response_text)
            if "Sector" in self.fd.keys():
                self.sector = self.fd["Sector"]
            else:
                self.fd = "No sector ID found"
            if ('MarketCapitalization' in self.fd.keys()):
                self.size = int(self.fd['MarketCapitalization'])
            else:
                self.size = -1
            # print(self.sector)
        else:
            print(f"Error fetching data for ticker {ticker}: {response.status_code}")
    
    def prepFactors(self):
        '''
        We probably ought to just do the analysis/marking for all potential factors in here
        then we can have a seperate analyze method that filters, sorts, and returns the stocks
        according whatever factors we want to consider
        '''
        # could use p/b instead
        if (float(self.fd["PriceToSalesRatioTTM"]) < 1):
            self.value = True
        
        if ((sizeLowerBound <= self.size) and (self.size <= sizeUpperBound)):
            self.sizeBool = True
        # the following is for calculating momentum
        # print(f"\n\nDebug for the momentum stuff:\n")
        # print(self.tsda.head())
        # Convert the 'timestamp' column to a datetime format and set it as the index
        self.tsda['timestamp'] = pd.to_datetime(self.tsda['timestamp'])
        # print("After converting timestamps:")
        # print(self.tsda.head())
        self.tsda = self.tsda.iloc[::-1]
        self.tsda = self.tsda.set_index('timestamp')
        # print("after changing index:")
        # print(self.tsda.head())
        # Calculate the daily percentage change in the adjusted close price
        self.tsda['pct_change'] = self.tsda['adjusted_close'].pct_change()
        # print("after calculating daily percentage")
        # print(self.tsda.head())

        # Calculate the 3-month momentum
        # 63 is an approximation of the number of trading days in 3 months
        momentum_3m = self.tsda['pct_change'].rolling(window=63).mean().iloc[-1]

        if (momentum_3m > 1.03):
            self.momentum_3m = True
        
        momentum_6m = self.tsda['pct_change'].rolling(window=175).sum().iloc[-1]
        if (momentum_6m > 1.05):
            self.momentum_6m = True

        self.momentum_1yr = self.tsda['pct_change'].rolling(window=175).mean().iloc[-1]
        

# list of stocks to analyze; atm adding these manually is worst part hahaha
# each stock produces 2 API calls, max free is 5 per minute and 500 per day PROBLEM
stocks = [Stock('AAPL'), Stock('F'), Stock('CSCO'), Stock('CROX'), Stock('JNJ'), Stock('XOM')]  # create a list of Stock objects

# basic for loop that will run our analysis
for obj in stocks:
    obj.fetch_data()
    obj.prepFactors()
    obj.printInfo()
    # basic preview of data
    # print(obj.tsda.head())
    # print(obj.tsda.tail())
    # print(obj.tsda.shape)
    # not the most beautiful way to print it but it is at least readable
    # for key in obj.fd:
        # print(f"{key}: {obj.fd[key]}")
    print("###########################################################################################################")
    '''
    Notes for myself:
    expected return is just: (1 + mean daily return)^250 - 1 *250 trading days per year*
    and the volatility is just the std dev of the mean daily returns
    we can perform weighted average to get expected return on portfolio
    for portfolio volatility: √(Σ (portfolio weight of member x (expected return member - Expected return of portfolio)^2))
    risk ~ volatility
    '''
    
