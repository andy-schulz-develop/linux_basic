
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Settings.Markets import timestamp_index, primary_value_index;


class Stop_Loss_Indicator(ActionNode):
    """
    Stop Loss Indicator
    Sends signal when latest price is below stop_loss_limit*100% of price <time_interval> ago.
    """

    def __init__(self, time_interval, stop_node, default_node, stop_loss_limit=0.5):
        """
        Constructor
        """
        super(Stop_Loss_Indicator, self).__init__(default_node=default_node);

        self._set_child(name=ChildrenNames.right_branch, node=stop_node);
        self._set_parameter(name="time_interval", parameter=time_interval);
        self._set_decimal_parameter("stop_loss_limit", parameter=stop_loss_limit);

    def _check_if_instance_is_initialized(self, data_array):
        if len(data_array) > self._minimum_number_of_points and \
                data_array[-1][timestamp_index] - data_array[0][timestamp_index] > self._parameters["time_interval"]:
            return True;
        else:
            return False;

    def __update_data(self, data_array: list):
        current_timestamp = data_array[-1][timestamp_index];
        self.__current_price = data_array[-1][primary_value_index];
        reference_time = max(data_array[0][timestamp_index],
                             current_timestamp - self._parameters["time_interval"]);

        reverse_iterator = reversed(data_array);
        iterator_content = next(reverse_iterator);
        while iterator_content[timestamp_index] > reference_time:
            iterator_content = next(reverse_iterator);
        price_at_reference_time = iterator_content[primary_value_index];
        self._calculation_result = price_at_reference_time * self._parameters["stop_loss_limit"];

    def check(self, data_array: list):
        self.__update_data(data_array);

        # Deciding what to do
        if self._calculation_result > self.__current_price:
            return self._children[ChildrenNames.right_branch];
        else:
            return self._children[ChildrenNames.default_branch];
