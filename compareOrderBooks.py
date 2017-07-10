from time import strftime, sleep
import krakenex
import gdax
import collections


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

    while True:
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
                print ("Ticker: " + ticker + ", Delta: " + str(spread.get_delta()
                                                               ) + ", Max Profit: " + str(spread.get_max_profit()) + ", Bid: " + gdax_bid[0] + ", BidVolume: " + gdax_bid[1] + ", Ask: " + kraken_ask[0] + ", AskVolume: " + kraken_ask[1])

            if (kraken_bid > gdax_ask):
                # normalize bid/ask data into floats and [price, volume only]
                spread = Spread(
                    ticker,
                    [float(kraken_bid[0]), float(kraken_bid[1])],
                    [float(gdax_ask[0]), float(gdax_ask[1])]
                )
                print ("Ticker: " + ticker + ", Delta: " + str(spread.get_delta()
                                                               ) + ", Max Profit: " + str(spread.get_max_profit()) + ", Bid: " + kraken_bid[0] + ", BidVolume: " + kraken_bid[1] + ", Ask: " + gdax_ask[0] + ", AskVolume: " + gdax_ask[1])

        sleep(10)


if __name__ == "__main__":
    main()
