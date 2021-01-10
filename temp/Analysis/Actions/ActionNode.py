"""
Created on Jun 3, 2018

@author: me
"""
from Settings.Markets import timestamp_index;
import decimal;
from enum import IntEnum;
# Just for type safety
from Analysis.Actions.IndicatorParameter import IndicatorParameter;


class ChildrenNames(IntEnum):
    left_branch = 1;
    default_branch = 2;
    right_branch = 3;
    analysis_node = 4;


class ActionNode(object):
    """
    class docs
    """

    def __init__(self, default_node):
        """
        Constructor
        """
        self._children = {};
        self._set_child(name=ChildrenNames.default_branch, node=default_node);
        self._parameters = {};
        self._minimum_number_of_points = 100;
        self._calculation_result = decimal.Decimal("0.0");
        self._last_timestamp = 0;
        self._tree_name = "";
        # Do not remove! at least one parameter is required in further code
        self._set_parameter(name="_name", parameter=self.__class__.__name__);

    def _set_child(self, name: ChildrenNames, node):
        if node is not None:
            self._children[name] = node;

    def _set_decimal_parameter(self, name: str, parameter):
        if parameter is not None:
            if isinstance(parameter, decimal.Decimal):
                self._parameters[name] = parameter;
            else:
                self._parameters[name] = decimal.Decimal(str(parameter));

    def _set_parameter(self, name: str, parameter):
        if parameter is not None:
            self._parameters[name] = parameter;

    def check(self, data_array: list):
        pass

    def get_calculation_result(self):
        return self._calculation_result;

    def get_indicator_name(self) -> str:
        return self._parameters["_name"];

    def get_parameters(self) -> dict:
        return self._parameters;

    def set_tree_name(self, name: str):
        self._tree_name = name;

    def get_tree_name(self) -> str:
        return self._tree_name;

    def get_all_tree_parameters(self) -> dict:
        current_parameters = self._parameters.copy();
        for child_name, child in self._children.items():
            if child is not None:
                current_parameters[child_name.name] = child.get_all_tree_parameters();
        return current_parameters;
    
    def get_max_tree_time_interval(self) -> int:
        if "time_interval" not in self._parameters:
            # TODO: Set proper default
            max_time_interval = 1000;
        else:
            max_time_interval = self._parameters["time_interval"];
        
        for child_name, child in self._children.items():
            if child.get_max_tree_time_interval() > max_time_interval:
                max_time_interval = child.get_max_tree_time_interval();
        return max_time_interval;

    def get_data_according_to_time_interval(self, data_array: list):
        # DEPRECATED??!? See filter_data_array
        if "time_interval" not in self._parameters:
            return data_array;
        else:
            starting_timestamp = data_array[-1][timestamp_index] - self._parameters["time_interval"];
            search_index = 0;
            data_point = data_array[search_index];
            while data_point[timestamp_index] < starting_timestamp:
                search_index += 1;
                data_point = data_array[search_index];
            # TODO: Consider raising a warning if the time_interval is bigger than the time covered in the data_array
            # if data_array[0][self._timestamp_index] >> starting_timestamp:
            # "Warning not enough data or too big time_interval"
            return data_array[search_index::];

    def print_tree_definition(self, indentation: int = 0) -> str:
        complete_text = "";
        max_key_length = len(max(self._parameters.keys(), key=len));
        indentation_string = " ".rjust(indentation);
        for key in sorted(self._parameters.keys()):
            complete_text += '\n' + indentation_string + key.ljust(max_key_length) + ": " + str(self._parameters[key]);
        for child_name in sorted(self._children.keys()):
            if self._children[child_name] is not None:
                complete_text += '\n' + indentation_string + child_name.name.ljust(max_key_length) + ": " + \
                                 self._children[child_name].print_tree_definition(indentation + max_key_length + 3);
        return complete_text;

    def update_parameter_in_tree_and_reset(self, indicator_parameter: IndicatorParameter) -> bool:
        self.reset_tree();
        return self.update_parameter(indicator_parameter=indicator_parameter);

    def update_parameter(self, indicator_parameter: IndicatorParameter) -> bool:
        identifier = indicator_parameter.get_identifier();
        target = identifier[0];
        if target in self._parameters:
            if isinstance(self._parameters[target], decimal.Decimal):
                self._parameters[target] = decimal.Decimal(str(indicator_parameter.get_value()));
            else:
                self._parameters[target] = indicator_parameter.get_value();
            return True;
        elif len(identifier) > 1 and target in self._children:
            return self._children[target].update_parameter(indicator_parameter.return_shortened_indicator_parameter());
        else:
            return False;

    def reset_tree(self):
        self.reset_values();
        for child_name, child in self._children.items():
            if child is not None:
                child.reset_tree();

    def reset_values(self):
        self._calculation_result = decimal.Decimal("0.0");
        self._last_timestamp = 0;

    def init_indicator(self, data_array) -> bool:
        children_initialized = self._check_if_instance_is_initialized(data_array=data_array);
        if children_initialized:
            self._last_timestamp = data_array[-1][timestamp_index];
            for child_name, child in self._children.items():
                children_initialized = children_initialized and child.init_indicator(data_array=data_array);
        return children_initialized;

    def shutdown_indicator(self):
        if len(self._children) > 0:
            for child_name, child in self._children.items():
                child.shutdown_indicator();

    def _check_if_instance_is_initialized(self, data_array: list) -> bool:
        return True;

    def filter_data_array(self, data_array: list) -> list:
        i = -1
        # Going back in time to last processed data point (or to the end of the list)
        while len(data_array) >= -1 * i and data_array[i][timestamp_index] > self._last_timestamp:
            i -= 1
        return data_array[i+1:];
