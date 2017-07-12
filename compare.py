from time import strftime, sleep, time
import krakenex
import gdax
from bittrex import bittrex
from google.cloud import datastore

import logging


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


def compare_order_books():
    # GDAX ticker symbols
    gdax_ticker = {"BTCtoUSD": "BTC-USD",
                   "ETHtoUSD": "ETH-USD",
                   "ETHtoBTC": "ETH-BTC",
                   #"LTCtoUSD": "LTC-USD",
                   "LTCtoBTC": "LTC-BTC"}

    # Kraken ticker symbols
    kraken_ticker = {"BTCtoUSD": "XXBTZUSD",
                     "ETHtoUSD": "XETHZUSD",
                     "ETHtoBTC": "XETHXXBT",
                     #"LTCtoUSD": "XLTCZUSD",
                     "LTCtoBTC": "XLTCXXBT"}

    # Bittrex ticker symbols
    bittrex_ticker = {"BTCtoUSD": "USDT-BTC",
                     "ETHtoUSD": "USDT-ETH",
                     "ETHtoBTC": "BTC-ETH",
                     "LTCtoBTC": "BTC-LTC"}

    # Construct default dict to store ask/bid prices of individual exchange

    k = krakenex.API()
    g = gdax.PublicClient()
    b = bittrex('9f7d4a9a4879422ababd4e2c1710b692', '3c4e4c0ab06a4ff7b9cc04cbbf7d82af')
    datastore_client = Datastore(datastore.Client())

    output = ""
    for ticker in gdax_ticker:
        try:
            # gdax: [price, size, num_orders]
            gdax_bid = (g.get_product_order_book(
                gdax_ticker[ticker]))["bids"][0]
            gdax_ask = (g.get_product_order_book(
                gdax_ticker[ticker]))["asks"][0]

            # kraken: [price, volume, timestamp]
            kraken_bid = (k.query_public('Depth', {'pair': kraken_ticker[ticker]}))[
                "result"][kraken_ticker[ticker]]["bids"][0]
            kraken_ask = (k.query_public('Depth', {'pair': kraken_ticker[ticker]}))[
                "result"][kraken_ticker[ticker]]["asks"][0]

            # bittrex: ['price', 'volumn']
            bittrex_bid = [(b.getorderbook(bittrex_ticker[ticker],'buy',depth=1))[0]['Rate'],
                               (b.getorderbook(bittrex_ticker[ticker],'buy',depth=1))[0]['Quantity'] ]
            bittrex_ask = [(b.getorderbook(bittrex_ticker[ticker],'sell',depth=1))[0]['Rate'],
                               (b.getorderbook(bittrex_ticker[ticker],'sell',depth=1))[0]['Quantity'] ]


            #print (gdax_bid, gdax_ask, kraken_bid, kraken_ask, bittrex_bid, bittrex_ask)

            # Key is exchange, Value is bid list: [price, volumn]
            dict_bid = {"GDAX": gdax_bid,
                        "Kraken": kraken_bid,
                        "Bittrex": bittrex_bid }

            # Key is exchange, Value is ask list: [price, volumn]
            dict_ask = {"GDAX": gdax_ask,
                        "Kraken": kraken_ask,
                        "Bittrex": bittrex_ask }

            for exchange_bid in dict_bid:

                for exchange_ask in dict_ask:

                    spread_stats = {}
                    bid = str(dict_bid[exchange_bid][0])
                    ask = str(dict_ask[exchange_ask][0])

                    if bid > ask:

                        bid_volume = str(dict_bid[exchange_bid][1])
                        ask_volume = str(dict_ask[exchange_ask][1])

                        spread = Spread(
                            ticker,
                            [float(bid), float(bid_volume)],
                            [float(ask), float(ask_volume)]
                        )
                        print ("Exchanges: " + exchange_bid + " to " + exchange_ask + ", Ticker: " + ticker + ", Delta: " + str(spread.get_delta()
                                                               ) + ", Max Profit: " + str(spread.get_max_profit()) + ", Bid: " + bid + ", BidVolume: " + bid_volume + ", Ask: " + ask + ", AskVolume: " + ask_volume)

                        spread_stats = {
                            "ticker": ticker,
                            "delta": spread.get_delta(),
                            "max_profit": spread.get_max_profit(),
                            "bid": bid,
                            "bid_volume": bid_volume,
                            "ask": ask,
                            "ask_volume": ask_volume,
                            "time": time()
                        }

                    string = ""
                    if spread_stats:
                        for stat in spread_stats:
                            string = string + stat + ": " + \
                                str(spread_stats[stat]) + ", "
                        output = output + string + " / "
                        print(string)
                        datastore_client.store(spread_stats)


        except:
            print("Error, continuing loop")

    return output


if __name__ == "__main__":
    compare_order_books()
