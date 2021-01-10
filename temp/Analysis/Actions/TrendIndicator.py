
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Settings.Markets import primary_value_index, timestamp_index;
import decimal;


class TrendIndicator(ActionNode):
    """
    class docs
    """

    def __init__(self,
                 upward_trend_node: ActionNode,
                 downward_trend_node: ActionNode,
                 default_node: ActionNode,
                 time_interval: int,
                 precision="0.00001"):
        """
        Constructor
        """
        super(TrendIndicator, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.left_branch, node=upward_trend_node);
        self._set_child(name=ChildrenNames.right_branch, node=downward_trend_node);

        self._set_decimal_parameter(name="precision", parameter=precision);
        self._set_parameter(name="time_interval", parameter=time_interval);

    def _check_if_instance_is_initialized(self, data_array: list):
        if data_array[-1][timestamp_index] - data_array[0][timestamp_index] > self._parameters["time_interval"]:
            return True;
        else:
            return False;

    def __update_data(self, data_array: list):
        current_timestamp = data_array[-1][timestamp_index];
        current_price = data_array[-1][primary_value_index];
        reference_time = max(data_array[0][timestamp_index], current_timestamp - self._parameters["time_interval"]);

        reverse_iterator = reversed(data_array);
        iterator_content = next(reverse_iterator);
        while iterator_content[timestamp_index] > reference_time:
            iterator_content = next(reverse_iterator);
        relative_price_difference = current_price / iterator_content[primary_value_index] - decimal.Decimal("1.0");
        time_difference = decimal.Decimal(current_timestamp - iterator_content[timestamp_index]);
        if time_difference > 0:
            self._calculation_result = relative_price_difference / time_difference;
        else:
            # TODO: Is assumption correct?
            self._calculation_result = decimal.Decimal("0.0");

    def check(self, data_array: list):
        self.__update_data(data_array=data_array);

        if self._calculation_result > self._parameters["precision"]:
            return self._children.get(ChildrenNames.left_branch);
        elif self._calculation_result < -1 * self._parameters["precision"]:
            return self._children.get(ChildrenNames.right_branch);
        else:
            return self._children.get(ChildrenNames.default_branch);
