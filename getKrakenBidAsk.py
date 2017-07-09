from time import strftime
import krakenex

tickers = ( "DASHEUR", "DASHUSD", "DASHXBT", "GNOETH", "GNOEUR", "GNOUSD", "GNOXBT", "USDTZUSD", "XETCXETH", "XETCXXBT", "XETCZEUR",
            "XETHXXBT", "XETHZCAD", "XETHZEUR", "XETHZGBP", "XETHZJPY", "XETHZUSD", "XICNXETH", "XICNXXBT", "XLTCXXBT", "XLTCZEUR", "XLTCZUSD",
            "XMLNXETH", "XMLNXXBT", "XREPXETH", "XREPXXBT", "XREPZEUR", "XREPZUSD", "XXBTZCAD", "XXBTZEUR", "XXBTZGBP", "XXBTZJPY", "XXBTZUSD",
            "XXDGXXBT", "XXLMXXBT", "XXLMZEUR", "XXLMZUSD", "XXMRXXBT", "XXMRZEUR", "XXMRZUSD", "XXRPXXBT", "XXRPZCAD", "XXRPZEUR", "XXRPZJPY",
	        "XXRPZUSD", "XZECXXBT", "XZECZEUR", "XZECZUSD" )

k = krakenex.API()

for t in tickers:

    ticker = k.query_public('Ticker', {'pair': t})
    depth = k.query_public('Depth', {'pair': t})

    last_close_raw = ticker["result"][t]["c"]
    last_ask_raw = ticker["result"][t]["a"]
    last_bid_raw = ticker["result"][t]["b"]
    last_close = last_close_raw[0]
    last_ask = last_ask_raw[0]
    last_bid = last_bid_raw[0]

    ask_depth = depth["result"][t]["asks"]
    bid_depth = depth["result"][t]["bids"]

    timenow = strftime("%H:%M:%S")
    print (timenow)
    print (t, ("last close = ", last_close), ("last ask = ", last_ask), ("last bid = ", last_bid) )
    print (t, ("lowest ask now = ", min(ask_depth)) )
    print (t, ("highest bid now = ", max(bid_depth)) )





