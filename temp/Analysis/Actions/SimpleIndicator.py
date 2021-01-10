
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Settings.Markets import primary_value_index;
from Tools.HelperFunctions import VERY_HIGH_DECIMAL;
import decimal;


class SimpleIndicator(ActionNode):
    """
    If the price is higher than the one before -> sell
    If the price is less than the one before -> buy
    """
    __last_buying_price = VERY_HIGH_DECIMAL;
    __last_selling_price = VERY_HIGH_DECIMAL;
    __bought_in = False;

    def __init__(self, oversold_node, overbought_node, default_node, change_limit=1.02):
        """
        Constructor
        """
        super(SimpleIndicator, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.right_branch, node=overbought_node);
        self._set_child(name=ChildrenNames.left_branch, node=oversold_node);
        self._set_decimal_parameter(name="change_limit", parameter=change_limit);

    def check(self, data_array):
        current_price = data_array[-1][primary_value_index];

        if current_price > self.__last_buying_price * self._parameters["change_limit"]:
            if self.__bought_in:  # Just sell if you have bought before
                self.__last_selling_price = current_price;
                self.__bought_in = False;
                return self._children.get(ChildrenNames.right_branch);
        elif current_price < self.__last_selling_price / self._parameters["change_limit"]:
            if not self.__bought_in:  # Just buy if you did not already buy before
                self.__last_buying_price = current_price;
                self.__bought_in = True;
                return self._children.get(ChildrenNames.left_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);

    def reset_values(self):
        self.__last_buying_price = VERY_HIGH_DECIMAL;
        self.__last_selling_price = VERY_HIGH_DECIMAL;
        self.__bought_in = False;


"""
    def print_tree_definition(self, prefix=None):
        if prefix is not None:
            result_string = prefix + self.__class__.__name__ + "(\n";
        else:
            result_string = self.__class__.__name__ + "(\n";
        indentation = " ".rjust(len(result_string)-1);
        result_string += indentation + "change_limit=" + str(self.__change_limit) + ",\n";

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
        super(SimpleIndicator, self).reset_values_in_tree(target_action_name=target_action_name,
                                                          parameter_package=parameter_package);
        if self._indicator_name.lower() == target_action_name.lower():
            if "change_limit" in parameter_package and parameter_package["change_limit"] is not None:
                self.__change_limit = decimal.Decimal(parameter_package["change_limit"]);
            self.__last_buying_price = VERY_HIGH_DECIMAL;
            self.__last_selling_price = VERY_HIGH_DECIMAL;
            self.__bought_in = False;
"""
