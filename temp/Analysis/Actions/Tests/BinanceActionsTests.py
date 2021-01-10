
import unittest;
import decimal;
import time;
from binance.client import Client;
from Analysis.Actions.BinanceActions import Buy, Sell;
from Tools.HelperFunctionsForTest import generate_input_data;

import Tools.LoggerCreator;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class BinanceActionsTests(unittest.TestCase):

    def test_overall(self):
        logger_creator = Tools.LoggerCreator.LoggerCreator();
        self._mylogger = logger_creator.createLogger(logfile_filename="test_log.log");

        # TODO: Use separate market settings
        api_key = "VP0zjQmHePtL1ezACLfMEK2eBAWZLfaHul2tIsZd3q621dCz3nFIaggHqeTaPqz7"
        api_secret = "0oFpLaiAqcodUrLuXwAQNXRc1rWwBl7wPDnlEcEmjomKzOhMZ4ZpVNBaAj4CYvAN"

        asset_symbol = "BNBETH";

        client = Client(api_key, api_secret, {"verify": False, "timeout": 20});
        client.ping();

        def get_bnb_account_balance(account_balance_type: str = "free"):
            return decimal.Decimal(client.get_asset_balance(asset="BNB").get(account_balance_type));

        def get_eth_account_balance(account_balance_type: str = "free"):
            return decimal.Decimal(client.get_asset_balance(asset="ETH").get(account_balance_type));

        def get_current_price():
            return decimal.Decimal(client.get_symbol_ticker(symbol=asset_symbol).get("price"));

        print(str(get_bnb_account_balance()));
        print(str(get_eth_account_balance()));

        buyer = Buy(coin_symbol=asset_symbol);
        seller = Sell(coin_symbol=asset_symbol);

        """
        # For manual testing:
        current_price = get_current_price();
        input_data = generate_input_data(number_of_steps=5, value=current_price);
        # buyer.check(data_array=input_data);
        seller.check(data_array=input_data);
        """

        # Test: Buy with far to low price afterwards sell/cancel - requires ETH > 0.01/price
        current_price = get_current_price();
        input_data = generate_input_data(number_of_steps=5, value=decimal.Decimal("0.1") * current_price);
        eth_start = get_eth_account_balance();
        buyer.check(data_array=input_data);
        self.assertGreater(eth_start, get_eth_account_balance());
        self.assertNotEqual(get_eth_account_balance("locked"), decimal.Decimal("0.0"));

        seller.check(data_array=input_data);
        self.assertEqual(eth_start, get_eth_account_balance());
        """
        # Test: Regular buy, hopefully successful
        current_price = get_current_price();
        input_data = generate_input_data(number_of_steps=5, value=current_price);
        eth_start_account_balance = get_eth_account_balance();
        bnb_start = get_bnb_account_balance();
        buyer.check(data_array=input_data);
        time.sleep(10);
        eth_account_balance = get_eth_account_balance();
        bnb_at_the_end = get_bnb_account_balance();
        self.assertGreater(bnb_at_the_end, bnb_start);
        self.assertGreater(eth_start_account_balance, eth_account_balance);

        # Test: Sell with far to high price afterwards buy/cancel - requires BNB
        current_price = get_current_price();
        input_data = generate_input_data(number_of_steps=5, value=decimal.Decimal("10.0") * current_price);
        bnb_start = get_bnb_account_balance();
        seller.check(data_array=input_data);
        bnb_in_between = get_bnb_account_balance();
        self.assertGreater(bnb_start, bnb_in_between);

        buyer.check(data_array=input_data);
        bnb_at_the_end = get_bnb_account_balance();
        self.assertEqual(bnb_start, bnb_at_the_end);

        # Test: Regular sell, hopefully successful
        current_price = get_current_price();
        input_data = generate_input_data(number_of_steps=5, value=current_price);
        eth_start_account_balance = get_eth_account_balance();
        bnb_start = get_bnb_account_balance();
        seller.check(data_array=input_data);
        time.sleep(10);
        eth_account_balance = get_eth_account_balance();
        bnb_at_the_end = get_bnb_account_balance();
        self.assertGreater(bnb_start, bnb_at_the_end);
        self.assertGreater(eth_account_balance, eth_start_account_balance);
        """

        print(str(get_bnb_account_balance()));
        print(str(get_eth_account_balance()));

        client.session.close();
        buyer.shutdown();
        seller.shutdown();

        """
        # this would result in verify: False and timeout: 5 for the get_all_orders call
        print(str(client.get_all_orders(symbol=asset_symbol)));  # , requests_params={'timeout': 5}
        print(str(client.get_asset_balance(asset=asset)));
        print(str(client.get_exchange_info()));
        print(str(client.get_system_status()));  # TODO: Execute on a regular basis to check status of binance
        print(str(client.get_symbol_info(asset_symbol)));
        print(str(client.get_account()));
        print(str(client.get_account_status()));  # TODO: Execute on a regular basis to check status of the account
        print(str(client.get_trade_fee(symbol=asset_symbol)));
        """
        """
        BNBETH
        0.103001 — 0.105355
        Day's Range
        """
        # self.assertAlmostEqual(first=eth_start_account_balance, second=eth_account_balance, places=3);


if __name__ == '__main__':
    unittest.main()

"""
{'baseAssetPrecision': 8,
'quoteOrderQtyMarketAllowed': True,
'ocoAllowed': True,
'status': 'TRADING',
'isSpotTradingAllowed': True,
'symbol': 'BNBETH',
'quoteCommissionPrecision': 8,
'isMarginTradingAllowed': True,
'baseCommissionPrecision': 8,
'icebergAllowed': True,
'quoteAsset': 'ETH',
'orderTypes': ['LIMIT', 'LIMIT_MAKER', 'MARKET', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT_LIMIT'],
'baseAsset': 'BNB',
'filters':
[{'tickSize': '0.00000100', 'minPrice': '0.00000100', 'filterType': 'PRICE_FILTER', 'maxPrice': '1000.00000000'},
{'multiplierUp': '5', 'filterType': 'PERCENT_PRICE', 'avgPriceMins': 5, 'multiplierDown': '0.2'},
{'maxQty': '90000000.00000000', 'minQty': '0.01000000', 'filterType': 'LOT_SIZE', 'stepSize': '0.01000000'},
{'applyToMarket': True, 'minNotional': '0.01000000', 'filterType': 'MIN_NOTIONAL', 'avgPriceMins': 5},
{'filterType': 'ICEBERG_PARTS', 'limit': 10},
{'maxQty': '68100.00000000', 'minQty': '0.00000000', 'filterType': 'MARKET_LOT_SIZE', 'stepSize': '0.00000000'},
{'maxNumAlgoOrders': 5, 'filterType': 'MAX_NUM_ALGO_ORDERS'}],
'quotePrecision': 8}
"""
