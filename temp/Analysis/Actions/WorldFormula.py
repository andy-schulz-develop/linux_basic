
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
import decimal;
from Settings.Markets import primary_value_index, timestamp_index;
from Analysis.Actions.TradeManagerFactory import trade_manager_factory;
from Tools.HelperFunctions import VERY_HIGH_DECIMAL;


class WorldFormula(ActionNode):
    """
    If the price is higher than the one before -> sell
    If the price is less than the one before -> buy
    """
    __price_minimum_in_interval = decimal.Decimal(0.0);
    __price_maximum_in_interval = VERY_HIGH_DECIMAL;
    __bought_in = False;
    __last_transaction_time = 0;
    # TODO: Put into settings
    __maximum_time_range_in_ms = 5 * 24 * 60 * 60 * 1000;  # 5 days

    def __init__(self,
                 oversold_node: ActionNode,
                 overbought_node: ActionNode,
                 default_node: ActionNode = None,
                 buy_in_limit=1.02,
                 sell_limit=0.99):
        """
        Constructor
        """
        super(WorldFormula, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.right_branch, node=overbought_node);
        self._set_child(name=ChildrenNames.left_branch, node=oversold_node);

        self._set_decimal_parameter(name="buy_limit", parameter=buy_in_limit);
        self._set_decimal_parameter(name="sell_limit", parameter=sell_limit);

        self.__trade_manager = None;

    def _check_if_instance_is_initialized(self, data_array: list) -> bool:
        if self.__trade_manager is None:
            self.__trade_manager = trade_manager_factory.get_current_trade_manager();
        if self.__trade_manager is None:
            return False;
        if len(data_array) < 10:
            return False;
        # Checking if time range of data_array covers time of last transaction and \
        # if last transaction was too long ago not all the time range will be covered (avoid buffer overflow)
        if data_array[0][timestamp_index] > self.__trade_manager.get_last_transaction_time() and \
                data_array[-1][timestamp_index] - data_array[0][timestamp_index] < self.__maximum_time_range_in_ms:
            return False;
        self.__sync_with_trade_manager();
        self.__update_parameters(data_array=data_array);
        return True;

    def __sync_with_trade_manager(self):
        if self.__last_transaction_time != self.__trade_manager.get_last_transaction_time():
            self.__bought_in = self.__trade_manager.is_bought_in();
            self._last_timestamp = self.__trade_manager.get_last_transaction_time();
            self.__last_transaction_time = self.__trade_manager.get_last_transaction_time();
            if self.__bought_in:
                self.__price_maximum_in_interval = self.__trade_manager.get_last_transaction_price();
            else:
                self.__price_minimum_in_interval = self.__trade_manager.get_last_transaction_price();

    def __update_parameters(self, data_array):
        filtered_data_array = self.filter_data_array(data_array=data_array);
        if self.__bought_in:
            for data_point in filtered_data_array:
                if data_point[primary_value_index] > self.__price_maximum_in_interval:
                    self.__price_maximum_in_interval = data_point[primary_value_index];
        else:
            for data_point in filtered_data_array:
                if data_point[primary_value_index] < self.__price_minimum_in_interval:
                    self.__price_minimum_in_interval = data_point[primary_value_index];
        self._last_timestamp = filtered_data_array[-1][timestamp_index];

    def check(self, data_array: list):
        self.__sync_with_trade_manager();
        self.__update_parameters(data_array=data_array);

        current_price = data_array[-1][primary_value_index];
        if self.__bought_in and current_price < self.__price_maximum_in_interval * self._parameters["sell_limit"]:
            self.__price_minimum_in_interval = current_price;
            self.__bought_in = False;
            self.__last_transaction_time = self._last_timestamp;
            return self._children.get(ChildrenNames.right_branch);
        elif not self.__bought_in and current_price > self.__price_minimum_in_interval * self._parameters["buy_limit"]:
            self.__price_maximum_in_interval = current_price;
            self.__bought_in = True;
            self.__last_transaction_time = self._last_timestamp;
            return self._children.get(ChildrenNames.left_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);

    def reset_values(self):
        super(WorldFormula, self).reset_values();
        self.__trade_manager = None;
        self.__price_minimum_in_interval = decimal.Decimal(0.0);
        self.__price_maximum_in_interval = VERY_HIGH_DECIMAL;
        self.__bought_in = False;
        self.__last_transaction_time = 0;
