
from Analysis.Actions.BinanceTradeManager import BinanceTradeManager;
# Just for type safety
from Analysis.Actions.TradeManager import TradeManager;


class TradeManagerFactory(object):

    __dict_of_trade_managers = {}

    def create_trade_manager(self, coin_symbol: str, logger_name: str = "application") -> TradeManager:
        if coin_symbol in self.__dict_of_trade_managers:
            return self.__dict_of_trade_managers.get(coin_symbol);
        else:
            self.__dict_of_trade_managers[coin_symbol] = BinanceTradeManager(coin_symbol=coin_symbol,
                                                                             logger_name=logger_name);
            return self.__dict_of_trade_managers.get(coin_symbol);

    def get_current_trade_manager(self) -> TradeManager:
        if self.__dict_of_trade_managers:
            return next(iter(self.__dict_of_trade_managers.values()));
        else:
            return None;

    def get_trade_manager_for_backtesting(self) -> TradeManager:
        return self.__dict_of_trade_managers.get("backtester_statistics");

    def set_trade_manager_for_backtesting(self, trade_manager: TradeManager):
        self.clear_trade_managers();
        self.__dict_of_trade_managers["backtester_statistics"] = trade_manager;

    def set_trade_manager(self, key: str, trade_manager: TradeManager):
        self.__dict_of_trade_managers[key] = trade_manager;

    def clear_trade_managers(self):
        self.__dict_of_trade_managers.clear();


trade_manager_factory = TradeManagerFactory();
