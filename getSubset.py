from utils import *
import keys as k
import pickle

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

fullset = getFullStockList(k.av_apikey)
for obj in fullset:
    print(f"On: {obj.symbol}")
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={obj.symbol}&datatype=json&apikey={k.av_apikey}"
    response = makeAPIcall(url)
    if response.status_code == 200:
        response_text = response.content.decode('utf-8')
        # print(f"\nresponse_text\n{response_text}\n\n")
        obj.fd = json.loads(response_text)
        # print(f"\nself.fd\n{obj.fd}\n\n")
        if isinstance(obj.fd, dict):
            if "Sector" in obj.fd.keys():
                obj.sector = obj.fd["Sector"]
            else:
                obj.sector = "No sector ID found"
            if "MarketCapitalization" in obj.fd.keys():
                try:
                    obj.size = int(obj.fd['MarketCapitalization'])
                except:
                    obj.size = -1
            else:
                obj.size = -1
        else:
            print(f"Error fetching data for ticker {obj.symbol}: {response.status_code}\nResponse content: {response_text}")
    else:
        print(f"Error fetching data for ticker {obj.symbol}: {response.status_code}")
    obj.analyze(sizeLowerBound, sizeUpperBound)
    print(f"Market cap: {obj.size}  bool: {obj.sizeBool}")

tickerlist = []
for obj in fullset:
    if obj.sizeBool:
        tickerlist.append(obj.symbol)


savelocation = "tickerlist.data"
print(f"{len(tickerlist)} stocks found in size range. ({sizeLowerBound}, {sizeUpperBound})")
print(f"Saving ticker list to {savelocation}")
with open(savelocation, "wb") as file:
    pickle.dump(tickerlist, file)
print("Print tickerlist:")
print(tickerlist)