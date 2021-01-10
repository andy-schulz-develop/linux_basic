
from enum import Enum;
import decimal;


class MarketOperation(Enum):
    buy = 1;
    sell = 2;


class TradeManager(object):

    def __init__(self):
        self._last_operation = None;
        self._last_transaction_price = decimal.Decimal("0.0");
        self._last_transaction_time = 0;
        self._sell_is_possible = True;

    def buy(self, data_array):
        pass;

    def sell(self, data_array):
        pass;

    def get_last_operation(self) -> MarketOperation:
        return self._last_operation;

    def is_bought_in(self) -> bool:
        if self._last_operation == MarketOperation.buy:
            return True;
        else:
            return False;

    def get_last_transaction_price(self) -> decimal.Decimal:
        return self._last_transaction_price;

    def get_last_transaction_time(self) -> int:
        return self._last_transaction_time;

    def sell_is_possible(self):
        return self._sell_is_possible;
