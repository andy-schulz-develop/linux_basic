
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Settings.Markets import timestamp_index, primary_value_index;
from operator import itemgetter;


class WilliamsR_Indicator(ActionNode):
    """
    The Williams %R oscillates from 0 to -100.
    When the indicator produces readings from 0 to -20, this indicates overbought market conditions.
    When readings are -80 to -100, it indicates oversold market conditions.
    """

    def __init__(self,
                 time_interval,
                 oversold_node,
                 overbought_node,
                 default_node,
                 overbought_limit=-20,
                 oversold_limit=-80):
        """
        Constructor
        """
        super(WilliamsR_Indicator, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.right_branch, node=overbought_node);
        self._set_child(name=ChildrenNames.left_branch, node=oversold_node);

        self._set_parameter(name="time_interval", parameter=time_interval);
        self._set_decimal_parameter(name="buy_limit", parameter=oversold_limit);
        self._set_decimal_parameter(name="sell_limit", parameter=overbought_limit);

        """
        Just use with caching mechanism below:
        self.__highest_price = None;
        self.__timestamp_of_highest_price = 0;
        self.__lowest_price = None;
        self.__timestamp_of_lowest_price = 0;
        """

    def _check_if_instance_is_initialized(self, data_array):
        if data_array[-1][timestamp_index] - data_array[0][timestamp_index] > self._parameters["time_interval"] and \
                len(data_array) > self._minimum_number_of_points:
            return True;
        else:
            return False;

    def check(self, data_array) -> ActionNode:
        self._calculation_result = None;
        list_of_data_points = self.get_data_according_to_time_interval(data_array);
        close_price = list_of_data_points[-1][primary_value_index];
        highest_price = max(list_of_data_points, key=itemgetter(primary_value_index))[primary_value_index];
        lowest_price = min(list_of_data_points, key=itemgetter(primary_value_index))[primary_value_index];
        if highest_price == lowest_price:  # Avoid division by zero in formula
            return self._children.get(ChildrenNames.default_branch);

        # CALCULATION
        # Formula: %R = (Highest High - Closing Price) / (Highest High - Lowest Low) x -100
        self._calculation_result = -1 * 100 * (highest_price - close_price) / (highest_price - lowest_price);

        """
        If this indicator is called for every data point use this caching mechanism:
        
        # If previous maximum is out of range,
        # find new overall max otherwise just compare new price with previous max price
        oldest_timestamp = list_of_data_points[0][timestamp_index];
        first_entry = list_of_data_points[0];
        if self.__timestamp_of_highest_price < oldest_timestamp:
            max_entry = max(list_of_data_points, key=itemgetter(primary_value_index));
            self.__highest_price = max_entry[primary_value_index];
            self.__timestamp_of_highest_price = max_entry[timestamp_index];
        elif close_price > self.__highest_price:
            self.__highest_price = close_price;
            self.__timestamp_of_highest_price = list_of_data_points[-1][timestamp_index];

            # If previous minimum is out of range,
            # find new overall min otherwise just compare new price with previous min price
        if self.__timestamp_of_lowest_price < oldest_timestamp:
            min_entry = min(list_of_data_points, key=itemgetter(primary_value_index));
            self.__lowest_price = min_entry[primary_value_index];
            self.__timestamp_of_lowest_price = min_entry[primary_value_index];
        elif close_price < self.__lowest_price:
            self.__lowest_price = close_price;
            self.__timestamp_of_lowest_price = list_of_data_points[-1][timestamp_index];
        """
        # Deciding what to do
        if self._calculation_result < self._parameters["buy_limit"]:
            return self._children.get(ChildrenNames.left_branch);
        elif self._calculation_result > self._parameters["sell_limit"]:
            return self._children.get(ChildrenNames.right_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);


"""
    def print_tree_definition(self, prefix=None):
        if prefix is not None:
            result_string = prefix + self.__class__.__name__ + "(\n";
        else:
            result_string = self.__class__.__name__ + "(\n";
        indentation = " ".rjust(len(result_string)-1);
        result_string += indentation + "time_interval=" + str(self._time_interval) + ",\n" + \
                         indentation + "buy_limit=" + str(self.__buy_limit) + ",\n" + \
                         indentation + "sell_limit=" + str(self.__sell_limit) + ",\n";
        result_string += self._print_child_node(node=self.__sell_node,
                                                node_name="right_branch",
                                                indentation=indentation) + ",\n";
        result_string += self._print_child_node(node=self._default_node,
                                                node_name="default_branch",
                                                indentation=indentation) + ",\n";
        result_string += self._print_child_node(node=self.__buy_node,
                                                node_name="left_branch",
                                                indentation=indentation) + ")";
        return result_string;

    def reset_values_in_tree(self, target_action_name, parameter_package):
        super(WilliamsR_Indicator, self).reset_values_in_tree(target_action_name=target_action_name,
                                                              parameter_package=parameter_package);
        if self._indicator_name.lower() == target_action_name.lower():
            if "buy_limit" in parameter_package and parameter_package["buy_limit"] is not None:
                self.__buy_limit = parameter_package["buy_limit"];
            if "sell_limit" in parameter_package and parameter_package["sell_limit"] is not None:
                self.__sell_limit = parameter_package["sell_limit"];
            if "time_interval" in parameter_package and parameter_package["time_interval"] is not None:
                self._time_interval = parameter_package["time_interval"];
"""
