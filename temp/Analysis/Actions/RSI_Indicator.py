
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Settings.Markets import timestamp_index, primary_value_index;
import decimal;


class RSI_Indicator(ActionNode):
    """
    RSI

    Aktien mit einem RSI von über 70 % werden als „überkauft“ betrachtet,
    Werte mit einem RSI unter 30 % als „überverkauft“.
    Manche Analysten passen diese Werte je nach Börsenumfeld an:

    in einem Bullenmarkt (Aufwärtstrend): Referenzlinie bei 40 (überverkauft) und 80 (überkauft)
    in einem Bärenmarkt (Abwärtstrend): Referenzlinie bei 20 (überverkauft) und 60 (überkauft)

    Allgemein wertet man das Erreichen oder das Überschreiten der
    Schwellenwerte Richtung Mittelbereich als eines mehrerer möglicher Kauf- bzw. Verkaufssignale.

    - https://de.wikipedia.org/wiki/Relative_Strength_Index
    """

    def __init__(self,
                 oversold_node,
                 overbought_node,
                 default_node,
                 time_interval,
                 buy_limit=0.3,
                 sell_limit=0.7):
        """
        Constructor
        """
        super(RSI_Indicator, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.right_branch, node=overbought_node);
        self._set_child(name=ChildrenNames.left_branch, node=oversold_node);

        self._set_parameter(name="time_interval", parameter=time_interval);
        self._set_decimal_parameter(name="buy_limit", parameter=buy_limit);
        self._set_decimal_parameter(name="sell_limit", parameter=sell_limit);

    def _check_if_instance_is_initialized(self, data_array):
        if data_array[-1][timestamp_index] - data_array[0][timestamp_index] > self._parameters["time_interval"] and \
                len(data_array) > self._minimum_number_of_points:
            return True;
        else:
            return False;

    def __calculate(self, data_array):
        sum_positive_changes = decimal.Decimal(0);
        sum_negative_changes = decimal.Decimal(0);
        list_of_data_points = self.get_data_according_to_time_interval(data_array);
        first_value = list_of_data_points[0][primary_value_index];
        for entry in list_of_data_points:
            difference = entry[primary_value_index] - first_value;
            if difference > 0:
                sum_positive_changes += difference;
            else:
                sum_negative_changes += difference;
            first_value = entry[primary_value_index];  # TODO: Check formula!!!
        if sum_positive_changes != sum_negative_changes:
            self._calculation_result = sum_positive_changes / (sum_positive_changes - sum_negative_changes);
        else:
            self._calculation_result = 0;  # TODO: Check if valid 10000

    def check(self, data_array):
        self.__calculate(data_array);

        if self._calculation_result > self._parameters["sell_limit"]:
            return self._children.get(ChildrenNames.right_branch);
        elif self._calculation_result < self._parameters["buy_limit"]:
            return self._children.get(ChildrenNames.left_branch);
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
        super(RSI_Indicator, self).reset_values_in_tree(target_action_name=target_action_name,
                                                        parameter_package=parameter_package);
        if self._indicator_name.lower() == target_action_name.lower():
            if "buy_limit" in parameter_package and parameter_package["buy_limit"] is not None:
                self.__buy_limit = decimal.Decimal(parameter_package["buy_limit"]) / decimal.Decimal(100);
            if "sell_limit" in parameter_package and parameter_package["sell_limit"] is not None:
                self.__sell_limit = decimal.Decimal(parameter_package["sell_limit"]) / decimal.Decimal(100);
            if "time_interval" in parameter_package and parameter_package["time_interval"] is not None:
                self._time_interval = parameter_package["time_interval"];
"""
