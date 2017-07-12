from time import strftime, sleep, time
import krakenex
import gdax
from bittrex import bittrex
from google.cloud import datastore
import http.client

import logging


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


class TradeExecutor:
    def __init__(self, gdax_auth_client, kraken_auth_client):
        # TODO get creds from separate file (key, b64secret, passphrase)
        self.gdax_auth_client = gdax_auth_client
        self.kraken_auth_client = kraken_auth_client

    def execute_spread(self, spread):
        volume_to_use = spread.get_effective_volume()
        # BID ORDER, EXECUTE SELL
        if spread.bid_exchange == "GDAX":
            ticker = gdax_ticker[spread.ticker]
            print ("Executing sell order on GDAX... Price: {}, Size: {}, Ticker: {}".format(
                str(spread.ask), str(volume_to_use), ticker))
            # TODO are these the best parameters? Maybe GTT and cancel after 5 minutes
            response = self.gdax_auth_client.sell(
                price=str(spread.ask),
                size=str(volume_to_use),
                product_id=ticker,
                time_in_force="IOC"
            )
            print (response)
        elif spread.bid_exchange == "Kraken":
            ticker = kraken_ticker[spread.ticker]
            print ("Executing sell order on Kraken... Price: {}, Size: {}, Ticker: {}".format(
                str(spread.ask), str(volume_to_use), ticker))
            response = self.kraken_auth_client.query_private("AddOrder", {
                "pair": ticker,
                "type": "buy",
                "ordertype": "limit",
                "price": str(spread.ask),
                "volume": str(volume_to_use),
                "expiretm": "+60"
            })
            print (response)

        # ASK ORDER, EXECUTE BUY
        if spread.ask_exchange == "GDAX":
            ticker = gdax_ticker[spread.ticker]
            print ("Executing buy order on GDAX... Price: {}, Size: {}, Ticker: {}".format(
                str(spread.bid), str(volume_to_use), ticker))
            # TODO are these the best parameters? Maybe GTT and cancel after 5 minutes
            response = self.gdax_auth_client.buy(
                price=str(spread.bid),
                size=str(volume_to_use),
                product_id=ticker,
                time_in_force="IOC"
            )
            print (response)
        elif spread.ask_exchange == "Kraken":
            ticker = kraken_ticker[spread.ticker]
            print ("Executing sell order on Kraken... Price: {}, Size: {}, Ticker: {}".format(
                str(spread.bid), str(volume_to_use), ticker))
            response = self.kraken_auth_client.query_private("AddOrder", {
                "pair": ticker,
                "type": "sell",
                "ordertype": "limit",
                "price": str(spread.bid),
                "volume": str(volume_to_use),
                "expiretm": "+60"
            })
            print (response)


class Spread:
    def __init__(self, ticker, bid, ask, bid_exchange, ask_exchange):
        # bid/ask format [price, volume]
        self.ticker = ticker
        self.bid = bid
        self.ask = ask
        self.bid_exchange = bid_exchange
        self.ask_exchange = ask_exchange

    # Delta is bid - ask. Bid is how much you can sell for,
    # ask is how little you can buy for, so we always want higher bids
    def get_delta(self):
        return self.bid[0] - self.ask[0]

    def get_effective_volume(self):
        volume_to_use = self.ask[1]
        if (self.bid[1] < self.ask[1]):
            volume_to_use = self.bid[1]
        return volume_to_use

    # Max profit is lesser of the two volumes times difference between bid and ask price
    def get_max_profit(self):
        volume_to_use = self.get_effective_volume()
        return (self.bid[0] - self.ask[0]) * volume_to_use

    def execute_spread(self):
        pass


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
    # Construct default dict to store ask/bid prices of individual exchange

    k = krakenex.API()
    g = gdax.PublicClient()
    b = bittrex('9f7d4a9a4879422ababd4e2c1710b692',
                '3c4e4c0ab06a4ff7b9cc04cbbf7d82af')
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
            bittrex_bid = [(b.getorderbook(bittrex_ticker[ticker], 'buy', depth=1))[0]['Rate'],
                           (b.getorderbook(bittrex_ticker[ticker], 'buy', depth=1))[0]['Quantity']]
            bittrex_ask = [(b.getorderbook(bittrex_ticker[ticker], 'sell', depth=1))[0]['Rate'],
                           (b.getorderbook(bittrex_ticker[ticker], 'sell', depth=1))[0]['Quantity']]

            # print (gdax_bid, gdax_ask, kraken_bid,
            #        kraken_ask, bittrex_bid, bittrex_ask)

            # Key is exchange, Value is bid list: [price, volumn]
            dict_bid = {"GDAX": gdax_bid,
                        "Kraken": kraken_bid,
                        "Bittrex": bittrex_bid}

            # Key is exchange, Value is ask list: [price, volumn]
            dict_ask = {"GDAX": gdax_ask,
                        "Kraken": kraken_ask,
                        "Bittrex": bittrex_ask}

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
                            [float(ask), float(ask_volume)],
                            exchange_bid,
                            exchange_ask
                        )

                        spread_stats = {
                            "ticker": ticker,
                            "delta": spread.get_delta(),
                            "max_profit": spread.get_max_profit(),
                            "bid": bid,
                            "bid_volume": bid_volume,
                            "ask": ask,
                            "ask_volume": ask_volume,
                            "effective_volume": spread.get_effective_volume(),
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
        except http.client.HTTPException as err:
            print ("Got error: " + err + " , continuing loop.")
            exit()

    return output


if __name__ == "__main__":
    compare_order_books()
