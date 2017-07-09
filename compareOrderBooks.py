from time import strftime
import krakenex
import gdax
import collections

# GDAX ticker symbols
GDAXTicker =   { "BTCtoUSD": "BTC-USD",
                  "ETHtoUSD": "ETH-USD",
                  "ETHtoBTC": "ETH-BTC",
                  "LTCtoUSD": "LTC-USD",
                  "LTCtoBTC": "LTC-BTC" }

# Kraken ticker symbols
krakenTicker = { "BTCtoUSD": "XXBTZUSD",
                  "ETHtoUSD": "XETHZUSD",
                  "ETHtoBTC": "XETHXXBT",
                  "LTCtoUSD": "XLTCZUSD",
                  "LTCtoBTC": "XLTCXXBT" }

# Construct default dict to store ask/bid prices of individual exchange
GDAXBidAsk = collections.defaultdict(dict)
KrakenBidAsk = collections.defaultdict(dict)

k = krakenex.API()
g = gdax.PublicClient()


for ticker in GDAXTicker:
    GDAXBidAsk[ticker]["bids"] = ((g.get_product_order_book(GDAXTicker[ticker]))["bids"][0][0])
    GDAXBidAsk[ticker]["asks"] = ((g.get_product_order_book(GDAXTicker[ticker]))["asks"][0][0])
    KrakenBidAsk[ticker]["bids"] = ((k.query_public('Depth', {'pair': krakenTicker[ticker]}))["result"][krakenTicker[ticker]]["bids"][0][0])
    KrakenBidAsk[ticker]["asks"] = ((k.query_public('Depth', {'pair': krakenTicker[ticker]}))["result"][krakenTicker[ticker]]["asks"][0][0])

    timenow = strftime("%H:%M:%S")

    # Check if GDAX bid is higher than Kraken ask
    if (GDAXBidAsk[ticker]["bids"]) > (KrakenBidAsk[ticker]["asks"]):
        print ("BID of GDAX " + ticker + " is higher than ASK of Kraken " +  ticker)
        print (timenow)
        print (GDAXBidAsk[ticker]["bids"])
        print (KrakenBidAsk[ticker]["asks"])

    # Check if Kraken bid is higher than GDAX ask
    elif (KrakenBidAsk[ticker]["bids"]) > (GDAXBidAsk[ticker]["asks"]):
        print ("BID of Kraken " + ticker + " is higher than ASK of GDX " +  ticker)
        print (timenow)
        print (KrakenBidAsk[ticker]["bids"])
        print (GDAXBidAsk[ticker]["asks"])

#Print both dictionaries
print (GDAXBidAsk)
print (KrakenBidAsk)





