
import time;
import decimal;
from decimal import Decimal;
from binance.client import Client;
from binance.exceptions import BinanceAPIException;
from binance.enums import TIME_IN_FORCE_GTC;
from Tools.LoggerCreator import LoggerCreator;
from Settings.Markets import binance as market;
from Settings.Markets import primary_value_index, timestamp_index;
from Tools.HelperFunctions import get_first_occurrence_in_list, get_current_timestamp, \
    return_human_readable_timestamp, VERY_HIGH_INTEGER, VERY_HIGH_DECIMAL;
from Tools.Monitor import SaveValue;
from Analysis.Actions.TradeManager import TradeManager, MarketOperation;
from Settings.ClassImplementations.SettingsReader import settings_reader;


class BinanceTradeManager(TradeManager):
    """
    class docs
    """

    def __init__(self, coin_symbol: str, logger_name: str = "application"):
        """
        Constructor
        """
        super(BinanceTradeManager, self).__init__();

        logger_name = logger_name + '.' + self.__class__.__name__.lower();
        self.__my_logger = LoggerCreator.createLogger(name=logger_name);
        self.__my_logger.info("Initialization started.");

        self.__coin_symbol = coin_symbol;
        # TODO: Put in settings?
        self.__max_retries = 40;
        self.__max_transfer_quantity_cap = {
            MarketOperation.buy: settings_reader.get_setting(class_name="BinanceTradeManager",
                                                             variable_name="tech_max_transfer_quantity_buy",
                                                             default=Decimal("0.0")),
            MarketOperation.sell: settings_reader.get_setting(class_name="BinanceTradeManager",
                                                              variable_name="tech_max_transfer_quantity_sell",
                                                              default=VERY_HIGH_DECIMAL)};  # Has to be HIGH!!
        self.__default_request_time_window = 10000;  # 10 seconds
        self.__max_time_lack_to_server = 1500;  # 1.5 seconds
        self.__looking_into_last_x_orders = 5;
        self.__locked_after_transaction = 10 * 1000;  # 10 seconds locked after a transaction

        self.__relevant_assets = {MarketOperation.buy: "",
                                  MarketOperation.sell: ""};
        self.__tech_max_transfer_quantity = {MarketOperation.buy: Decimal("0.0"), MarketOperation.sell: Decimal("0.0")};
        self.__tech_min_transfer_quantity = Decimal("0.0");
        self.__min_notional_limit = Decimal("0.0");
        self.__tech_quantity_step_size = Decimal("0.0");
        self.__tech_max_price = Decimal("0.0");
        self.__tech_min_price = Decimal("0.0");
        self.__tech_price_step_size = Decimal("0.0");
        self.__account_balances_for_ = {MarketOperation.buy: Decimal("0.0"),
                                        MarketOperation.sell: Decimal("0.0")};
        self.__list_of_open_orders = [];
        self.__transfer_quantity = Decimal("0.0");
        self.__latest_market_price = Decimal("0.0");
        self.__latest_incoming_timestamp = 0;
        self.__price = Decimal("0.0");
        self.__symbol_information = None;
        self.__locked = False;
        self.__is_shutdown = False;
        self.__client = None;
        self.__transaction_lock = False;
        self._last_transaction_time = VERY_HIGH_INTEGER;  # Has to be HIGH!!

        self.__asset_for_buying = SaveValue(name_prefix="usdt_asset",
                                            database=market.get_monitor_database_settings(),
                                            logger_name=logger_name);
        self.__asset_for_selling = SaveValue(name_prefix=coin_symbol.lower() + "_sell_asset",
                                             database=market.get_monitor_database_settings(),
                                             logger_name=logger_name);
        self.__transaction_price = SaveValue(name_prefix=coin_symbol.lower() + "_transaction_price",
                                             database=market.get_monitor_database_settings(),
                                             logger_name=logger_name);
        self.__total_amount = SaveValue(name_prefix=coin_symbol.lower() + "_converted",
                                        database=market.get_monitor_database_settings(),
                                        logger_name=logger_name);
        self.__gain_per_sell = SaveValue(name_prefix=coin_symbol.lower() + "_sell_gain",
                                         database=market.get_monitor_database_settings(),
                                         logger_name=logger_name);
        self.__my_logger.info("Initialization finished.");
        self.__symbol_information = self.__return_symbol_information();
        self.fetch_data();

    def __connect(self):
        self.__my_logger.debug("Opening request session to Binance.");
        self.__client = Client(market.get_login_credentials().get("api_key"),
                               market.get_login_credentials().get("api_secret"),
                               {"verify": True, "timeout": 20});

    def __disconnect(self):
        self.__my_logger.debug("Closing request session to Binance.");
        self.__client.session.close();

    def wait_for_unlock(self):
        count = 0;
        while self.__locked and count < self.__max_retries:
            self.__my_logger.debug("Waiting for unlock");
            time.sleep(1);
            count += 1;
        if count >= self.__max_retries:
            self.__my_logger.warning("Connection to Binance seems broken!");
            raise ConnectionError("Connection to Binance seems broken!");

    def sell_if_no_incoming_data(self):
        # TODO: Put 1800000 into __init__()
        if get_current_timestamp() - self.__latest_incoming_timestamp > 1800000:
            self.sell(data_array=[(Decimal("0.0"), Decimal("0.0"), Decimal("0.0"), Decimal("0.0"),
                                   self.__latest_market_price, Decimal("0.0"), Decimal("0.0"), Decimal("0.0"),
                                   Decimal("0.0"), Decimal("0.0"), Decimal("0.0"), Decimal("0.0"), Decimal("0.0"),
                                   Decimal("0.0"), Decimal("0.0"), 0, get_current_timestamp(), 0, 0, 0)]);

    def __return_symbol_information(self):
        asset_required_for_buying = self.__relevant_assets[MarketOperation.buy];
        asset_required_for_selling = self.__relevant_assets[MarketOperation.sell];
        return {"Asset required for buying": asset_required_for_buying,
                "Asset required for selling": asset_required_for_selling,
                "Technical minimum transfer quantity": self.__tech_min_transfer_quantity,
                "Technical maximum transfer quantity for buying":
                    self.__tech_max_transfer_quantity[MarketOperation.buy],
                "Technical maximum transfer quantity for selling":
                    self.__tech_max_transfer_quantity[MarketOperation.sell],
                "Technical step size of transfer quantity": self.__tech_quantity_step_size,
                "Technical step size of price": self.__tech_price_step_size,
                "Minimum notional limit": self.__min_notional_limit,
                "Account balance of " + asset_required_for_buying: self.__account_balances_for_[MarketOperation.buy],
                "Account balance of " + asset_required_for_selling: self.__account_balances_for_[MarketOperation.sell],
                "Last order placed at": return_human_readable_timestamp(self._last_transaction_time),
                "Last transaction price": self._last_transaction_price};

    def __log_data_if_changed(self):
        symbol_information = self.__return_symbol_information();
        if self.__symbol_information != symbol_information:
            self.__my_logger.info("Symbol information for " + self.__coin_symbol + " changed.");
            self.__my_logger.info("Before: " + str(self.__symbol_information));
            self.__my_logger.info("After: " + str(symbol_information));
            self.__symbol_information = symbol_information;
            self.__asset_for_buying.save_value(value=self.__account_balances_for_[MarketOperation.buy]);
            self.__asset_for_selling.save_value(value=self.__account_balances_for_[MarketOperation.sell]);
            self.__total_amount.\
                save_value(value=self.__account_balances_for_[MarketOperation.sell] * self._last_transaction_price)
            self.__transaction_price.save_value(value=self._last_transaction_price);
        else:
            self.__my_logger.info("Nothing changed.");

    def __update_last_order_data(self, timestamp: int, price: Decimal, operation: str):
        if timestamp < self._last_transaction_time or \
                self._last_transaction_time + 5000 < timestamp:
            self._last_transaction_time = timestamp;
            if price < Decimal("0.3") * self.__latest_market_price:
                self._last_transaction_price = self.__latest_market_price;
            else:
                self._last_transaction_price = price;
            if operation.upper() == "BUY":
                self._last_operation = MarketOperation.buy;
            elif operation.upper() == "SELL":
                self._last_operation = MarketOperation.sell;

    def __update_last_valid_order(self):
        """
        REQUIRES ACTIVE BINANCE CONNECTION!

        Return of client.get_all_orders() function:
        [{'origQuoteOrderQty': '0.00000000', 'price': '0.09938600', 'orderId': 133608029,
         'cummulativeQuoteQty': '0.05466230', 'icebergQty': '0.00000000', 'orderListId': -1,
         'stopPrice': '0.00000000', 'updateTime': 1580575928617, 'status': 'FILLED', 'time': 1580575854220,
         'timeInForce': 'GTC', 'isWorking': True, 'origQty': '0.55000000', 'clientOrderId': 'aoRlG4DE5wXy2L9RbayLea',
         'executedQty': '0.55000000', 'type': 'LIMIT', 'symbol': 'BNBETH', 'side': 'BUY'}]

         Documentation of order status:
         https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md#enum-definitions
         Possible values: NEW, FILLED, PARTIALLY_FILLED, CANCELED, PENDING_CANCEL, REJECTED, EXPIRED
        """
        valid_order_status = ["NEW", "FILLED", "PARTIALLY_FILLED", "CANCELED"];
        last_valid_order = {};
        i = -1;
        # Looking for last valid (not rejected/expired) order
        while last_valid_order.get("status") not in valid_order_status:
            list_of_all_orders = self.__client.get_all_orders(symbol=self.__coin_symbol,
                                                              limit=self.__looking_into_last_x_orders);
            length = len(list_of_all_orders);
            while length + 1 + i > 0 and last_valid_order.get("status") not in valid_order_status:
                last_valid_order = list_of_all_orders[i];
                i -= 1;
            if last_valid_order.get("status") not in valid_order_status:
                self.__looking_into_last_x_orders += 5;
                if self.__looking_into_last_x_orders > 100:
                    error_message = "There is no valid order within the last 100 orders! Place a valid order manually";
                    self.__my_logger.warning(error_message);
                    raise Exception(error_message);

        # Creating virtual order if last order was canceled otherwise simply updating last transaction values
        if last_valid_order["status"].upper() == "CANCELED":
            operation = "SELL";
            if last_valid_order.get("side").upper() == "SELL":
                operation = "BUY";
            self.__update_last_order_data(timestamp=int(last_valid_order["updateTime"]),
                                          price=self.__price,
                                          operation=operation);
        else:
            self.__update_last_order_data(timestamp=int(last_valid_order["time"]),
                                          price=Decimal(str(last_valid_order.get("price"))),
                                          operation=last_valid_order.get("side").upper());

    def __update_account_balances(self):
        """
                REQUIRES ACTIVE BINANCE CONNECTION!
        Return of client.get_asset_balance() function:
        {'asset': 'COTI', 'free': '0.00000000', 'locked': '0.00000000'}
        """
        temp = self.__client.get_asset_balance(asset=self.__relevant_assets[MarketOperation.buy],
                                               recvWindow=self.__default_request_time_window);
        self.__account_balances_for_[MarketOperation.buy] = Decimal(temp["free"]);
        temp = self.__client.get_asset_balance(asset=self.__relevant_assets[MarketOperation.sell],
                                               recvWindow=self.__default_request_time_window);
        self.__account_balances_for_[MarketOperation.sell] = Decimal(temp["free"]);
        if self.__account_balances_for_[MarketOperation.sell] < self.__tech_min_transfer_quantity:
            self._sell_is_possible = False;
        else:
            self._sell_is_possible = True;

    def __check_time_lack_to_binance_server(self):
        """
                REQUIRES ACTIVE BINANCE CONNECTION!
        """
        time_lack_to_server = int(time.time() * 1000) - self.__client.get_server_time().get('serverTime');
        if time_lack_to_server > self.__max_time_lack_to_server:
            self.__my_logger.warning("Time lack to server is very high: " + str(time_lack_to_server));

    def __update_filter_parameters(self):
        """
        REQUIRES ACTIVE BINANCE CONNECTION!

        Documentation:
        https://github.com/binance-exchange/binance-official-api-docs/blob/master/rest-api.md
        """
        self.__latest_market_price = Decimal(self.__client.get_symbol_ticker(symbol=self.__coin_symbol).get("price"));
        symbol_info = self.__client.get_symbol_info(symbol=self.__coin_symbol);

        # Converting and formatting data to use it later
        filter_data = get_first_occurrence_in_list(source_list=symbol_info["filters"],
                                                   key="filterType",
                                                   value="LOT_SIZE",
                                                   default={});
        relative_price_filter_data = get_first_occurrence_in_list(source_list=symbol_info["filters"],
                                                                  key="filterType",
                                                                  value="PERCENT_PRICE",
                                                                  default={});
        price_filter_data = get_first_occurrence_in_list(source_list=symbol_info["filters"],
                                                         key="filterType",
                                                         value="PRICE_FILTER",
                                                         default={});
        min_notional_filter_data = get_first_occurrence_in_list(source_list=symbol_info["filters"],
                                                                key="filterType",
                                                                value="MIN_NOTIONAL",
                                                                default={});
        if min_notional_filter_data.get("applyToMarket"):  # "applyToMarket" is a bool
            self.__min_notional_limit = Decimal(min_notional_filter_data.get("minNotional"));
        else:
            self.__min_notional_limit = Decimal("0.0");
        absolute_max_price = Decimal(price_filter_data.get("maxPrice", "999999999.99"));
        max_price_calculated = Decimal(
            relative_price_filter_data.get("multiplierUp", "100.0")) * self.__latest_market_price * Decimal("0.99");
        absolute_min_price = Decimal(price_filter_data.get("minPrice", "0.0"));
        min_price_calculated = Decimal(
            relative_price_filter_data.get("multiplierDown", "0.0")) * self.__latest_market_price * Decimal("1.01");
        self.__tech_max_price = min(absolute_max_price, max_price_calculated);
        self.__tech_min_price = max(absolute_min_price, min_price_calculated);
        self.__relevant_assets[MarketOperation.buy] = symbol_info["quoteAsset"];
        self.__relevant_assets[MarketOperation.sell] = symbol_info["baseAsset"];
        self.__tech_min_transfer_quantity = Decimal(filter_data["minQty"].strip("0"));
        self.__tech_max_transfer_quantity[MarketOperation.buy] = min(
            Decimal(filter_data["maxQty"].strip("0")), self.__max_transfer_quantity_cap[MarketOperation.buy]);
        self.__tech_max_transfer_quantity[MarketOperation.sell] = min(
            Decimal(filter_data["maxQty"].strip("0")), self.__max_transfer_quantity_cap[MarketOperation.sell]);
        self.__tech_price_step_size = Decimal(price_filter_data["tickSize"].strip("0"));
        self.__tech_quantity_step_size = Decimal(filter_data["stepSize"].strip("0"));

    def __update_open_orders(self):
        self.__list_of_open_orders = self.__client.get_open_orders(symbol=self.__coin_symbol,
                                                                   recvWindow=self.__default_request_time_window);

    def fetch_data(self):
        if self.__locked:
            self.__my_logger.warning("Data is currently locked! Not fetching data.");
        else:
            self.__locked = True;
            self.__my_logger.info("Fetching data from binance.");
            self.__connect();
            self.__check_time_lack_to_binance_server();
            self.__update_filter_parameters();
            self.__update_account_balances();
            self.__update_last_valid_order();
            self.__update_open_orders();

            self.__disconnect();
            self.check_transaction_lock();
            self.__locked = False;
            self.__log_data_if_changed();

    def check_transaction_lock(self):
        if self.__transaction_lock:
            if get_current_timestamp() > self._last_transaction_time + self.__locked_after_transaction:
                self.__transaction_lock = False;
        return self.__transaction_lock;

    def __cancel_single_order(self, order) -> bool:
        self.__my_logger.info("Canceling " + order["side"].lower() + " order with order ID " +
                              str(order["orderId"]) + " for coin " + self.__coin_symbol);
        try:
            self.__client.cancel_order(symbol=self.__coin_symbol,
                                       orderId=order["orderId"],
                                       recvWindow=self.__default_request_time_window);
        except BinanceAPIException as exception:
            if exception.code == -2011:
                self.__my_logger.warning("Order with orderId " + str(order["orderId"]) + " does not exist. " +
                                         "It might have been filled.")
                self.__update_open_orders();
                return False;
            else:
                self.__my_logger.warning("Exception occurred while trying to cancel orders!");
                raise exception;
        return True;

    def cancel_stale_orders(self, operation: MarketOperation) -> bool:
        account_balance_has_to_be_updated = False;
        orders_to_be_removed = MarketOperation.buy;
        if len(self.__list_of_open_orders) > 0:
            self.__update_open_orders();
        if operation == MarketOperation.buy:
            orders_to_be_removed = MarketOperation.sell;
        i = 0;
        while i < len(self.__list_of_open_orders):
            order = self.__list_of_open_orders[i];
            i += 1;
            if order["side"].lower() == orders_to_be_removed.name.lower():
                account_balance_has_to_be_updated = True;
                if not self.__cancel_single_order(order=order):
                    i = 0;  # If cancellation did not take place restarting while loop
        if account_balance_has_to_be_updated:
            self.__update_last_valid_order();
        return account_balance_has_to_be_updated;

    def cancel_all_orders(self):
        """
        Exception when order does not exist:
        binance.exceptions.BinanceAPIException: APIError(code=-2011): Unknown order sent
        :return:
        """
        account_balance_has_to_be_updated = False;
        if len(self.__list_of_open_orders) > 0:
            self.__update_open_orders();
        while len(self.__list_of_open_orders) > 0:
            account_balance_has_to_be_updated = True;
            order = self.__list_of_open_orders.pop(0);
            self.__cancel_single_order(order=order);
        if account_balance_has_to_be_updated:
            self.__update_account_balances();
            self.__update_last_valid_order();

    def check_if_transaction_data_is_valid(self, operation: MarketOperation) -> bool:
        if self.check_transaction_lock():
            wait_time_in_sec = (self.__locked_after_transaction +
                                self._last_transaction_time - get_current_timestamp()) / 1000.0;
            self.__my_logger.warning("Transactions are currently locked. Transaction not possible! Please wait " +
                                     str(wait_time_in_sec) + "sec");
            return False;
        if self.__transfer_quantity < self.__tech_min_transfer_quantity:
            self.__my_logger.warning("Transfer quantity is too low. Transaction not possible!" +
                                     " | Minimum transfer quantity: " + str(self.__tech_min_transfer_quantity) +
                                     " | Requested transfer quantity: " + str(self.__transfer_quantity));
            return False;
        elif self.__transfer_quantity * self.__price < self.__min_notional_limit:
            self.__my_logger.warning("Notional (=transfer_quantity * price) is too low. Transaction not possible!" +
                                     " | Minimum notional: " + str(self.__min_notional_limit) +
                                     " | Current notional: " + str(self.__transfer_quantity * self.__price));
            return False;
        else:
            return True;

    def set_price(self, data_array):
        self.__price = data_array[-1][primary_value_index];
        if self.__price > self.__tech_max_price:
            self.__my_logger.warning("Price is too high. Reducing it to maximum price." +
                                     " | Maximum price: " + str(self.__tech_max_price) +
                                     " | Requested price: " + str(self.__price));
            self.__price = self.__tech_max_price;
        if self.__price < self.__tech_min_price:
            self.__my_logger.warning("Price is too low. Increasing it to minimum price." +
                                     " | Minimum price: " + str(self.__tech_min_price) +
                                     " | Requested price: " + str(self.__price));
            self.__price = self.__tech_min_price;
        self.__price = self.__price.quantize(self.__tech_price_step_size);

    def set_transfer_quantity(self, operation: MarketOperation):
        transfer_quantity = Decimal("0.0");
        if operation == MarketOperation.sell:
            transfer_quantity = self.__account_balances_for_[MarketOperation.sell];

            # This if-command is currently not required but this might change in the future
            if transfer_quantity > self.__account_balances_for_[operation]:
                self.__my_logger.warning("Account balance is too low. Reducing transfer quantity to account balance." +
                                         " | Account balance: " + str(self.__account_balances_for_[operation]) +
                                         " | Requested transfer quantity: " + str(transfer_quantity));
                transfer_quantity = self.__account_balances_for_[operation];
        else:
            transfer_quantity = self.__account_balances_for_[MarketOperation.buy] / self.__price;

        if transfer_quantity > self.__tech_max_transfer_quantity[operation]:
            self.__my_logger.warning(
                "Transfer quantity is too high. Reducing it to maximum transfer quantity." +
                " | Maximum transfer quantity: " + str(self.__tech_max_transfer_quantity[operation]) +
                " | Requested transfer quantity: " + str(transfer_quantity));
            transfer_quantity = self.__tech_max_transfer_quantity[operation];

        self.__transfer_quantity = transfer_quantity.quantize(self.__tech_quantity_step_size,
                                                              rounding=decimal.ROUND_DOWN);

    def __prepare_operation(self, data_array, operation: MarketOperation) -> bool:
        self.wait_for_unlock();
        self.__locked = True;
        self.__connect();
        self.__latest_incoming_timestamp = data_array[-1][timestamp_index];
        self.cancel_stale_orders(operation=operation);
        # Has to be after cancel_stale_orders (in case trade is canceled)
        self.__update_account_balances();
        self.set_price(data_array=data_array);
        # Has to be after __update_account_balances (in case balance changes quickly)
        self.set_transfer_quantity(operation=operation);
        return self.check_if_transaction_data_is_valid(operation=operation);

    def __finish_operation(self, order_response, operation: MarketOperation):
        """
        :param order_response: {'type': 'LIMIT', 'fills': [], 'orderListId': -1, 'orderId': 382239791,
        'timeInForce': 'GTC', 'transactTime': 1584708302780, 'origQty': '3.00000000',
        'clientOrderId': 'shjLkBExGcyJUHhF8wBDrQ', 'executedQty': '0.00000000', 'side': 'BUY', 'price': '13.07380000',
        'symbol': 'BNBUSDT', 'cummulativeQuoteQty': '0.00000000', 'status': 'NEW'}
        :param operation:
        :return:
        """
        if isinstance(order_response, dict) and "orderListId" in order_response and "clientOrderId" in order_response:
            if operation == MarketOperation.sell and self._last_operation == MarketOperation.buy:
                self.__gain_per_sell.save_value(
                    value=self.__price/self._last_transaction_price*Decimal("100.0")-Decimal("100.0"));
            self._last_operation = operation;
            self._last_transaction_price = self.__price;
            self._last_transaction_time = self.__latest_incoming_timestamp;
            self.__transaction_lock = True;
        self.__my_logger.info("Response: " + str(order_response));
        self.__update_account_balances();
        self.__update_open_orders();
        self.__disconnect();
        self.__log_data_if_changed();
        self.__locked = False;

    def __handle_binance_api_exception(self, exception: BinanceAPIException, operation: MarketOperation):
        exception_message = str(exception);
        if exception.code == -1021:
            self.__my_logger.warning("Timestamp for this request is outside of the recvWindow. See: " +
                                     exception_message + " Restarting...");
            """
            Problem: Timestamp for this request is outside of the recvWindow
            Causes:
            The timestamp sent is outside of the serverTime - recvWindow value
            The timestamp sent is more than 1000ms ahead of the server time
            This may occur if your computer time is not correct.
            Restart may help
            """
            self.__disconnect();
            raise exception;
        elif exception.code == -2014:
            # TODO: !!!!!
            print("Hahaha " + exception_message);
            return True;
        elif exception.code == -1013:
            """
            Exception:
            binance.exceptions.BinanceAPIException: APIError(code=-1013): Filter failure: MIN_NOTIONAL
            The MIN_NOTIONAL filter defines the minimum notional value allowed for an order on a symbol.
            An order's notional value is the price * quantity.
            """
            error_message = "Notional (=transfer_quantity * price) is slightly too low. Transaction not possible!" +\
                            " | Current notional: " + str(self.__transfer_quantity * self.__price);
            self.__my_logger.error(error_message);
            self.__finish_operation(order_response=error_message, operation=MarketOperation.sell);
        elif exception.code == -2010:
            """
            binance.exceptions.BinanceAPIException:
            APIError(code=-2010): Account has insufficient balance for requested action
            """
            self.__update_account_balances();
            self.set_transfer_quantity(operation=operation)
            return True;
        else:
            self.__my_logger.warning("Error occurred: " + exception_message + "| Resetting connection and retrying.");
            self.__disconnect();
            time.sleep(2.0);
            self.__connect();
            return True;

    def buy(self, data_array):
        order_response = None;
        self.__my_logger.info("Starting buy process.");
        if self.__prepare_operation(data_array=data_array, operation=MarketOperation.buy):
            self.__my_logger.info("Buying into " + self.__coin_symbol +
                                  ", Price: " + str(self.__price) +
                                  ", Amount: " + str(self.__transfer_quantity));
            try:
                order_response = self.__client.order_limit_buy(symbol=self.__coin_symbol,
                                                               quantity=float(self.__transfer_quantity),
                                                               price=str(self.__price),
                                                               timeInForce=TIME_IN_FORCE_GTC,
                                                               recvWindow=self.__default_request_time_window);
            except BinanceAPIException as e:
                if self.__handle_binance_api_exception(exception=e, operation=MarketOperation.buy):
                    order_response = self.__client.order_limit_buy(symbol=self.__coin_symbol,
                                                                   quantity=float(self.__transfer_quantity),
                                                                   price=str(self.__price),
                                                                   timeInForce=TIME_IN_FORCE_GTC,
                                                                   recvWindow=self.__default_request_time_window * 2);
        self.__finish_operation(order_response=order_response, operation=MarketOperation.buy);

    def sell(self, data_array):
        order_response = None;
        self.__my_logger.info("Starting sell process.");
        if self.__prepare_operation(data_array=data_array, operation=MarketOperation.sell):
            self.__my_logger.info("Selling from " + self.__coin_symbol +
                                  ", Price: " + str(self.__price) +
                                  ", Amount: " + str(self.__transfer_quantity));
            try:
                order_response = self.__client.order_limit_sell(symbol=self.__coin_symbol,
                                                                quantity=float(self.__transfer_quantity),
                                                                price=str(self.__price),
                                                                timeInForce=TIME_IN_FORCE_GTC,
                                                                recvWindow=self.__default_request_time_window);
            except BinanceAPIException as e:
                if self.__handle_binance_api_exception(exception=e, operation=MarketOperation.buy):
                    order_response = self.__client.order_limit_sell(symbol=self.__coin_symbol,
                                                                    quantity=float(self.__transfer_quantity),
                                                                    price=str(self.__price),
                                                                    timeInForce=TIME_IN_FORCE_GTC,
                                                                    recvWindow=self.__default_request_time_window * 2);
        self.__finish_operation(order_response=order_response, operation=MarketOperation.sell);

    def sell_all(self, data_array: list):
        temp_max_transfer_quantity = self.__tech_max_transfer_quantity[MarketOperation.sell];
        self.__tech_max_transfer_quantity[MarketOperation.sell] = VERY_HIGH_DECIMAL;
        self.sell(data_array=data_array);
        self.__tech_max_transfer_quantity[MarketOperation.sell] = temp_max_transfer_quantity;

    def shutdown(self):
        if self.__is_shutdown:
            self.__my_logger.info("Binance Trade Manager is already shutdown.");
        else:
            self.__my_logger.info("Shutting down Binance Trade Manager.");
            self.__asset_for_selling.shutdown_monitor();
            # self.__asset_for_buying.shutdown_monitor();
            self.__is_shutdown = True;
