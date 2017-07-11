from time import strftime, sleep, time
import krakenex
import gdax
from google.cloud import datastore


class Spread:
    def __init__(self, ticker, bid=0, ask=0):
        # bid/ask format [price, volume]
        self.bid = bid
        self.ask = ask

        self.ticker = ticker

    # Delta is bid - ask. Bid is how much you can sell for,
    # ask is how little you can buy for, so we always want higher bids
    def get_delta(self):
        return self.bid[0] - self.ask[0]

    def get_delta_percentage(self):
        return

    # Max profit is lesser of the two volumes times difference between bid and ask price
    def get_max_profit(self):
        volume_to_use = self.ask[1]
        if (self.bid[1] < self.ask[1]):
            volume_to_use = self.bid[1]
        # print ("Volume: " + str(volume_to_use) + " Bid: " + str(self.bid[0]) + " Ask: " + str(self.ask[0]) + " Delta: " + str(self.bid[0] - self.ask[0]))
        return (self.bid[0] - self.ask[0]) * volume_to_use


class Datastore:
    def __init__(self, client, kind="Spread"):
        self.client = client
        self.kind = kind

    # entity_props is a dict
    def store(self, entity_props):
        key = self.client.key(self.kind)
        entity = datastore.Entity(key=key)
        for entity_key in entity_props:
            entity[entity_key] = entity_props[entity_key]
        self.client.put(entity)


def datastore_config():
    # Instantiates a client
    datastore_client = datastore.Client()


def main():
    # GDAX ticker symbols
    gdax_ticker = {"BTCtoUSD": "BTC-USD",
                   "ETHtoUSD": "ETH-USD",
                   "ETHtoBTC": "ETH-BTC",
                   "LTCtoUSD": "LTC-USD",
                   "LTCtoBTC": "LTC-BTC"}

    # Kraken ticker symbols
    kraken_ticker = {"BTCtoUSD": "XXBTZUSD",
                     "ETHtoUSD": "XETHZUSD",
                     "ETHtoBTC": "XETHXXBT",
                     "LTCtoUSD": "XLTCZUSD",
                     "LTCtoBTC": "XLTCXXBT"}

    # Construct default dict to store ask/bid prices of individual exchange

    k = krakenex.API()
    g = gdax.PublicClient()
    datastore_client = Datastore(datastore.Client())

    for ticker in gdax_ticker:
        # [price, size, num_orders]
        gdax_bid = (g.get_product_order_book(
            gdax_ticker[ticker]))["bids"][0]
        gdax_ask = (g.get_product_order_book(
            gdax_ticker[ticker]))["asks"][0]

        # [price, volume, timestamp]
        kraken_bid = (k.query_public('Depth', {'pair': kraken_ticker[ticker]}))[
            "result"][kraken_ticker[ticker]]["bids"][0]
        kraken_ask = (k.query_public('Depth', {'pair': kraken_ticker[ticker]}))[
            "result"][kraken_ticker[ticker]]["asks"][0]

        # print (gdax_bid, gdax_ask, kraken_bid, kraken_ask)
        if (gdax_bid > kraken_ask):
            # normalize bid/ask data into floats and [price, volume only]
            spread = Spread(
                ticker,
                [float(gdax_bid[0]), float(gdax_bid[1])],
                [float(kraken_ask[0]), float(kraken_ask[1])]
            )
            spread_stats = {
                "ticker": ticker,
                "delta": spread.get_delta(),
                "max_profit": spread.get_max_profit(),
                "bid": gdax_bid[0],
                "bid_volume": gdax_bid[1],
                "ask": kraken_ask[0],
                "ask_volume": kraken_ask[1],
                "time": time()
            }

        if (kraken_bid > gdax_ask):
            # normalize bid/ask data into floats and [price, volume only]
            spread = Spread(
                ticker,
                [float(kraken_bid[0]), float(kraken_bid[1])],
                [float(gdax_ask[0]), float(gdax_ask[1])]
            )
            print ("Ticker: " + ticker + ", Delta: " + str(spread.get_delta()
                                                           ) + ", Max Profit: " + str(spread.get_max_profit()) + ", Bid: " + kraken_bid[0] + ", BidVolume: " + kraken_bid[1] + ", Ask: " + gdax_ask[0] + ", AskVolume: " + gdax_ask[1])

            spread_stats = {
                "ticker": ticker,
                "delta": spread.get_delta(),
                "max_profit": spread.get_max_profit(),
                "bid": kraken_bid[0],
                "bid_volume": kraken_bid[1],
                "ask": gdax_ask[0],
                "ask_volume": gdax_ask[1],
                "time": time()
            }

        string = ""
        for stat in spread_stats:
            string = string + stat + ": " + str(spread_stats[stat]) + ", "
        print(string)
        datastore_client.store(spread_stats)


if __name__ == "__main__":
    main()
