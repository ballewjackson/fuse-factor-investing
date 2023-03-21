import pandas as pd
import io as io
import requests
import json
import time


start_time = time.time()
minuteCallCount = 0
dailyminuteCallCount = 0
maxCallsPerMinute = 5
maxCallsPerDay = 500
def makeAPIcall(url):
    global totalCallCount, minuteCallCount, dailyminuteCallCount, start_time, maxCallsPerMinute, maxCallsPerDay
    # print("In call manager. Count:", minuteCallCount, "\tDelta Time:", time.time() - start_time)
    if minuteCallCount >= maxCallsPerMinute:
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            # print("In sleep. Sleeping for:", 60-elapsed_time)
            time.sleep(60 - elapsed_time)
        minuteCallCount = 0
        start_time = time.time()
    
    if dailyminuteCallCount >= maxCallsPerDay:
        elapsed_time = time.time() - start_time
        if elapsed_time < 86400:
            # print("In sleep. Sleeping for:", 86400-elapsed_time)
            time.sleep(86400 - elapsed_time)
        dailyminuteCallCount = 0
        start_time = time.time()

    # Make the API call and increment the counter
    response = requests.get(url)
    minuteCallCount += 1
    dailyminuteCallCount += 1
    totalCallCount += 1
    return response

def getsymbols(apikey):
    url = f'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={apikey}'
    response = makeAPIcall(url)
    if response.status_code == 200:
        response_text = response.content.decode('utf-8')
        response_text = io.StringIO(response_text)
        stockDF = pd.read_csv(response_text)
        return stockDF
    else:
        print("Failed getting stock list from AlphaVantage API.")

class Stock:
    def __init__(self, symbol):
        self.symbol = symbol
        self.tsda = None
        self.fd = {}
        self.sector = ""
        self.size = -1
        self.sizeBool = False
        self.value = False
        self.momentum_3m = False
        self.momentum_6m = False
        self.momentum_1yr = 0
        self.dividend = -1
        
    def printInfo(self):
        print(f"\n{self.fd['Name']}: {self.symbol}  {self.sector}  Size: {self.size}")
        print(f"Value: {self.value}\t3M Momentum: {self.momentum_3m}")
        print(f"6M Momentum: {self.momentum_6m}\t1YR Momentum: {self.momentum_1yr}")

    def fetch_data(self, apikey):
        ticker = self.symbol
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&datatype=csv&apikey={apikey}"
        response = makeAPIcall(url)
        if response.status_code == 200:
            response_text = response.content.decode('utf-8')
            self.tsda = pd.read_csv(io.StringIO(response_text))
        else:
            print(f"Error fetching data for ticker {ticker}: {response.status_code}")

        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&datatype=json&apikey={apikey}"
        response = makeAPIcall(url)
        if response.status_code == 200:
            response_text = response.content.decode('utf-8')
            # print(f"\nresponse_text\n{response_text}\n\n")
            self.fd = json.loads(response_text)
            # print(f"\nself.fd\n{self.fd}\n\n")
            if isinstance(self.fd, dict):
                if "Sector" in self.fd.keys():
                    self.sector = self.fd["Sector"]
                else:
                    self.sector = "No sector ID found"
                if "MarketCapitalization" in self.fd.keys():
                    try:
                        self.size = int(self.fd['MarketCapitalization'])
                    except:
                        self.size = -1
                else:
                    self.size = -1
            else:
                print(f"Error fetching data for ticker {ticker}: {response.status_code}\nResponse content: {response_text}")
        else:
            print(f"Error fetching data for ticker {ticker}: {response.status_code}")

    def analyze(self, sizeLowerBound, sizeUpperBound):
        try:
            if (float(self.fd["PriceToSalesRatioTTM"]) < 1):
                self.value = True
        except:
            try:
                if (float(self.fd['PricetoBookRation']) < 1):
                    self.value = True
            except:
                self.value = False
        if ((sizeLowerBound <= self.size) and (self.size <= sizeUpperBound)):
            self.sizeBool = True
        self.tsda['timestamp'] = pd.to_datetime(self.tsda['timestamp'])
        self.tsda = self.tsda.iloc[::-1]
        self.tsda = self.tsda.set_index('timestamp')
        self.tsda['pct_change'] = self.tsda['adjusted_close'].pct_change()

        # Calculate the 3-month momentum
        # 63 is an approximation of the number of trading days in 3 months
        momentum_3m = self.tsda['pct_change'].rolling(window=63).mean().iloc[-1]
        if (momentum_3m > 0):
            self.momentum_3m = True
        
        momentum_6m = self.tsda['pct_change'].rolling(window=175).sum().iloc[-1]
        if (momentum_6m > 0):
            self.momentum_6m = True

        self.momentum_1yr = self.tsda['pct_change'].rolling(window=175).mean().iloc[-1]

        if "DividendYield" in self.fd.keys():
            self.dividend = self.fd['DividendYield']
