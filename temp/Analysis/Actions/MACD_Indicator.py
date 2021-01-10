"""
Version from 26.10.2019
"""
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Analysis.Actions.Moving_Averages.ExponentialMovingAverages import CachedEMA, TimeDependentEma;
from Settings.Markets import timestamp_index, primary_value_index;
import decimal;


class MACDIndicator(ActionNode):
    """
    MACD_Indicator as defined by Wikipedia:
    https://de.wikipedia.org/wiki/MACD

    MACD(l_slow, l_fast)(t) = EMA(t, l_fast) - EMA(t, l_slow)
    Signal(l_signal)(t) = EMA(MACD(l_slow, l_fast)(t), l_signal)
    Weight: alpha = 2 / (l + 1)
    Buy if: MACD(t-1) < Signal(t-1) and MACD(t) > Signal(t)
    - Instead of using Signal(t) it is also common to use just y = 0 (Is not applied here)
    """

    def __init__(self,
                 oversold_node: ActionNode,
                 overbought_node: ActionNode,
                 default_node: ActionNode,
                 macd_ema_time_interval=10,
                 slow_ema_time_interval=400,
                 fast_ema_time_interval=2,
                 precision=0.00000001):
        """
        Constructor
        """
        super(MACDIndicator, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.right_branch, node=overbought_node);
        self._set_child(name=ChildrenNames.left_branch, node=oversold_node);

        self._set_decimal_parameter(name="precision", parameter=precision);
        self._set_decimal_parameter(name="slow_ema", parameter=slow_ema_time_interval);
        self._set_decimal_parameter(name="fast_ema", parameter=fast_ema_time_interval);
        self._set_decimal_parameter(name="macd_ema", parameter=macd_ema_time_interval);

        self.__slow_ema = None;
        self.__fast_ema = None;
        self.__macd_ema = None;
        self._calculation_result = decimal.Decimal("0.0");
        self._minimum_number_of_points = 10;

        self.reset_values();

    def reset_values(self):
        super(MACDIndicator, self).reset_values();
        self.__slow_ema = CachedEMA(time_parameter=self._parameters["slow_ema"],
                                    precision=self._parameters["precision"]);
        self.__fast_ema = CachedEMA(time_parameter=self._parameters["fast_ema"],
                                    precision=self._parameters["precision"]);
        self.__macd_ema = CachedEMA(time_parameter=self._parameters["macd_ema"],
                                    precision=self._parameters["precision"]);
        self._minimum_number_of_points = 10;  # TODO: Set a good default
        self._minimum_number_of_points = max([self._minimum_number_of_points,
                                              self.__slow_ema.get_minimum_number_of_points(),
                                              self.__fast_ema.get_minimum_number_of_points(),
                                              self.__macd_ema.get_minimum_number_of_points()]);

    def _check_if_instance_is_initialized(self, data_array: list) -> bool:
        if len(data_array) > self._minimum_number_of_points:
            initial_price = data_array[0][primary_value_index];
            self.__slow_ema.init_calculation(initial_price=initial_price);
            self.__fast_ema.init_calculation(initial_price=initial_price);
            self.__macd_ema.init_calculation(initial_price=decimal.Decimal(0.0));
            self._last_timestamp = data_array[0][timestamp_index];
            self._calculate(data_array=data_array);
            return True;
        else:
            return False;

    def _calculate(self, data_array):
        macd_value = decimal.Decimal(0.0);
        # Going back in time to last processed data point (or to the end of the list)
        filtered_data_array = self.filter_data_array(data_array=data_array);
        for data_point in filtered_data_array:
            price = data_point[primary_value_index];
            macd_value = self.__fast_ema.calculation_step(price=price) - self.__slow_ema.calculation_step(price=price);
            self.__macd_ema.calculation_step(price=macd_value);
        self._last_timestamp = data_array[-1][timestamp_index];
        self._calculation_result = self.__macd_ema.get_ema() - macd_value;

    def check(self, data_array: list) -> ActionNode:
        previous_calculation_result = self._calculation_result;
        self._calculate(data_array);

        if self._calculation_result > 0 > previous_calculation_result:
            return self._children.get(ChildrenNames.right_branch);
        elif self._calculation_result < 0 < previous_calculation_result:
            return self._children.get(ChildrenNames.left_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);


class TimeDependentMACDIndicator(MACDIndicator):
    """
    TimeDependentMACDIndicator
    """
    def __init__(self,
                 oversold_node: ActionNode,
                 overbought_node: ActionNode,
                 default_node: ActionNode,
                 macd_ema_time_interval=10,
                 slow_ema_time_interval=400,
                 fast_ema_time_interval=2,
                 precision=0.00000001):
        """
        Constructor
        """
        super(TimeDependentMACDIndicator, self).__init__(oversold_node=oversold_node,
                                                         overbought_node=overbought_node,
                                                         default_node=default_node,
                                                         macd_ema_time_interval=macd_ema_time_interval,
                                                         slow_ema_time_interval=slow_ema_time_interval,
                                                         fast_ema_time_interval=fast_ema_time_interval,
                                                         precision=precision);

    def reset_values(self):
        self.__slow_ema = TimeDependentEma(time_parameter=self._parameters["slow_ema"],
                                           precision=self._parameters["precision"]);
        self.__fast_ema = TimeDependentEma(time_parameter=self._parameters["fast_ema"],
                                           precision=self._parameters["precision"]);
        self.__macd_ema = TimeDependentEma(time_parameter=self._parameters["macd_ema"],
                                           precision=self._parameters["precision"]);
        self._calculation_result = decimal.Decimal("0.0");
        self._minimum_number_of_points = 10;  # TODO: Set a good default
        self._minimum_number_of_points = max([self._minimum_number_of_points,
                                              self.__slow_ema.get_minimum_number_of_points(),
                                              self.__fast_ema.get_minimum_number_of_points(),
                                              self.__macd_ema.get_minimum_number_of_points()]);

    def _check_if_instance_is_initialized(self, data_array: list) -> bool:
        if len(data_array) > self._minimum_number_of_points:
            initial_price = data_array[0][primary_value_index];
            initial_timestamp = data_array[0][timestamp_index];
            self.__slow_ema.init_calculation(initial_timestamp=initial_timestamp, initial_price=initial_price);
            self.__fast_ema.init_calculation(initial_timestamp=initial_timestamp, initial_price=initial_price);
            self.__macd_ema.init_calculation(initial_timestamp=initial_timestamp, initial_price=decimal.Decimal(0.0));
            self._last_timestamp = initial_timestamp;
            self._calculate(data_array=data_array);
            return True;
        else:
            return False;

    def _calculate(self, data_array):
        macd_value = decimal.Decimal(0.0);
        # Going back in time to last processed data point (or to the end of the list)
        filtered_data_array = self.filter_data_array(data_array=data_array);
        for data_point in filtered_data_array:
            price = data_point[primary_value_index];
            timestamp = data_point[timestamp_index];
            macd_value = self.__fast_ema.calculation_step(timestamp=timestamp, price=price) - \
                self.__slow_ema.calculation_step(timestamp=timestamp, price=price);
            self.__macd_ema.calculation_step(timestamp=timestamp, price=macd_value);
        self._last_timestamp = data_array[-1][timestamp_index];
        self._calculation_result = macd_value - self.__macd_ema.get_ema();


class ReverseMACDIndicator(MACDIndicator):
    """
    TimeDependentMACDIndicator
    """
    def __init__(self,
                 oversold_node: ActionNode,
                 overbought_node: ActionNode,
                 default_node: ActionNode,
                 macd_ema_time_interval=10,
                 slow_ema_time_interval=400,
                 fast_ema_time_interval=2,
                 precision=0.00000001):
        """
        Constructor
        """
        super(ReverseMACDIndicator, self).__init__(oversold_node=oversold_node,
                                                   overbought_node=overbought_node,
                                                   default_node=default_node,
                                                   macd_ema_time_interval=macd_ema_time_interval,
                                                   slow_ema_time_interval=slow_ema_time_interval,
                                                   fast_ema_time_interval=fast_ema_time_interval,
                                                   precision=precision);

    def check(self, data_array: list) -> ActionNode:
        previous_calculation_result = self._calculation_result;
        self._calculate(data_array);

        if self._calculation_result < 0 < previous_calculation_result:
            return self._children.get(ChildrenNames.right_branch);
        elif self._calculation_result > 0 > previous_calculation_result:
            return self._children.get(ChildrenNames.left_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);


class ReverseTimeDependentMACDIndicator(TimeDependentMACDIndicator):
    """
    TimeDependentMACDIndicator
    """
    def __init__(self,
                 oversold_node: ActionNode,
                 overbought_node: ActionNode,
                 default_node: ActionNode,
                 macd_ema_time_interval=10,
                 slow_ema_time_interval=400,
                 fast_ema_time_interval=2,
                 precision=0.00000001):
        """
        Constructor
        """
        super(ReverseTimeDependentMACDIndicator, self).__init__(oversold_node=oversold_node,
                                                                overbought_node=overbought_node,
                                                                default_node=default_node,
                                                                macd_ema_time_interval=macd_ema_time_interval,
                                                                slow_ema_time_interval=slow_ema_time_interval,
                                                                fast_ema_time_interval=fast_ema_time_interval,
                                                                precision=precision);

    def check(self, data_array: list) -> ActionNode:
        previous_calculation_result = self._calculation_result;
        self._calculate(data_array);

        if self._calculation_result < 0 < previous_calculation_result:
            return self._children.get(ChildrenNames.right_branch);
        elif self._calculation_result > 0 > previous_calculation_result:
            return self._children.get(ChildrenNames.left_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);
