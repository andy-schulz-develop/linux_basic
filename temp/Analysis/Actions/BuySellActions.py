
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Analysis.Actions.TradeManagerFactory import trade_manager_factory;
from Settings.Markets import primary_value_index;
import decimal;


class BuySellAction(ActionNode):
    """
    class docs
    """

    def __init__(self, coin_symbol: str, default_node: ActionNode = None):
        """
        Constructor
        """
        super(BuySellAction, self).__init__(default_node=default_node);

        self._coin_symbol = coin_symbol;
        self._trade_manager = None;

    def _check_if_instance_is_initialized(self, data_array: list) -> bool:
        if self._trade_manager is None:
            self._trade_manager = trade_manager_factory.get_current_trade_manager();
        if len(data_array) > 10 and self._trade_manager is not None:
            return True;
        else:
            return False;

    def reset_values(self):
        super(BuySellAction, self).reset_values();
        self._trade_manager = None;


class Buy(BuySellAction):
    """
    Buys
    """

    def __init__(self, coin_symbol: str, default_node: ActionNode = None):
        """
        Constructor
        """
        super(Buy, self).__init__(coin_symbol=coin_symbol, default_node=default_node);

    def check(self, data_array) -> ActionNode:
        self._trade_manager.buy(data_array=data_array);
        return self._children.get(ChildrenNames.default_branch);


class Sell(BuySellAction):
    """
    Sells
    """

    def __init__(self, coin_symbol: str, default_node: ActionNode = None):
        """
        Constructor
        """
        super(Sell, self).__init__(coin_symbol=coin_symbol, default_node=default_node);

    def check(self, data_array):
        self._trade_manager.sell(data_array=data_array);
        return self._children.get(ChildrenNames.default_branch);


class EmergencyBuy(BuySellAction):
    """
    Connects to Binance, cancels all active orders and buys
    """

    def __init__(self, coin_symbol: str, default_node: ActionNode = None):
        """
        Constructor
        """
        super(EmergencyBuy, self).__init__(coin_symbol=coin_symbol, default_node=default_node);

    def check(self, data_array) -> ActionNode:
        self._trade_manager.cancel_all_orders();
        self._trade_manager.buy(data_array=data_array);
        return self._children.get(ChildrenNames.default_branch);


class EmergencySell(BuySellAction):
    """
    Connects to Binance, cancels all active orders and sells
    """

    def __init__(self, coin_symbol: str, default_node: ActionNode = None):
        """
        Constructor
        """
        super(EmergencySell, self).__init__(coin_symbol=coin_symbol, default_node=default_node);

    def check(self, data_array):
        self._trade_manager.cancel_all_orders();
        self._trade_manager.sell_all(data_array=data_array);
        return self._children.get(ChildrenNames.default_branch);


class EmergencySell2(BuySellAction):
    """
    Connects to Binance, cancels all active orders and sells with even lower price
    """

    def __init__(self, coin_symbol: str, default_node: ActionNode = None):
        """
        Constructor
        """
        super(EmergencySell2, self).__init__(coin_symbol=coin_symbol, default_node=default_node);
        # TODO: Put 0.97 into settings???
        self.__decreasing_factor = decimal.Decimal("0.97");

    def check(self, data_array):
        self._trade_manager.cancel_all_orders();
        latest_data_point = list(data_array[-1]);
        latest_data_point[primary_value_index] *= self.__decreasing_factor;
        self._trade_manager.sell_all(data_array=[tuple(latest_data_point)]);
        return self._children.get(ChildrenNames.default_branch);
