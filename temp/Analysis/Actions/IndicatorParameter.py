
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Tools.Database_Handler import Database_Writer;
from Tools.HelperFunctions import get_current_timestamp;
# Just for type safety
from Settings.ClassImplementations.Database import DatabaseSettings;


class IndicatorParameter(object):

    def __init__(self, tuple_or_identifier: tuple, value=None):
        list_of_entries = [];
        if not isinstance(tuple_or_identifier, tuple):
            raise TypeError("'tuple_or_identifier' is not a tuple, but should be one!");
        if len(tuple_or_identifier) < 1:
            raise TypeError("'tuple_or_identifier' is empty!");

        if value is None:
            if not isinstance(tuple_or_identifier[0], tuple):
                raise TypeError("'tuple_or_identifier[0]' is not a tuple, but should be one!");
            self.__value = tuple_or_identifier[1];
            pre_identifier = tuple_or_identifier[0];
        else:
            self.__value = value;
            pre_identifier = tuple_or_identifier;

        for entry in pre_identifier:
            if isinstance(entry, int):
                list_of_entries.append(self.convert_int_to_children_name(entry));
            elif isinstance(entry, str):
                list_of_entries.append(self.convert_string_to_children_name(entry));
            else:
                list_of_entries.append(entry);
        self.__identifier = tuple(list_of_entries);

    def get_int_identifier(self) -> tuple:
        list_of_entries = []
        for entry in self.__identifier:
            if isinstance(entry, ChildrenNames):
                list_of_entries.append(self.convert_children_name_to_int(entry));
            else:
                list_of_entries.append(entry);
        return tuple(list_of_entries);

    def get_identifier_for_database(self):
        return str(self.get_int_identifier());

    def get_identifier(self) -> tuple:
        return self.__identifier;

    def get_value(self):
        return self.__value;

    def return_shortened_indicator_parameter(self):
        if len(self.__identifier) > 1:
            return IndicatorParameter(tuple_or_identifier=self.__identifier[1:], value=self.__value);
        else:
            return IndicatorParameter(tuple_or_identifier=tuple(), value=self.__value);

    @staticmethod
    def convert_children_name_to_int(children_name: ChildrenNames) -> int:
        return int(children_name);

    @staticmethod
    def convert_children_name_to_string(children_name: ChildrenNames) -> str:
        return children_name.__name__;

    @staticmethod
    def convert_string_to_children_name(name_string: str):
        name_string = name_string.lower();
        if "left_branch" in name_string:
            return ChildrenNames.left_branch;
        elif "default_branch" in name_string:
            return ChildrenNames.default_branch;
        elif "right_branch" in name_string:
            return ChildrenNames.right_branch;
        elif "analysis_node" in name_string:
            return ChildrenNames.analysis_node;
        else:
            return name_string;

    @staticmethod
    def convert_int_to_children_name(name_int: int) -> ChildrenNames:
        return ChildrenNames(name_int);

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return str(self.__identifier) < str(other.get_identifier());

    def __le__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return str(self.__identifier) <= str(other.get_identifier());

    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return str(self.__identifier) > str(other.get_identifier());

    def __ge__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return str(self.__identifier) >= str(other.get_identifier());

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return str(self.__identifier) == str(other.get_identifier());


class IndicatorParameterSet(object):

    def __init__(self, coin_symbol: str, indicator_tree_name: str, init_indicator_parameters=None):
        self.__coin_symbol = coin_symbol;
        self.__indicator_tree_name = indicator_tree_name
        self.__indicator_parameters = [];
        # Type checking of optional input list
        if init_indicator_parameters is not None:
            if isinstance(init_indicator_parameters, tuple) or isinstance(init_indicator_parameters, list):
                if len(init_indicator_parameters) > 0 and isinstance(init_indicator_parameters[0], IndicatorParameter):
                    self.__indicator_parameters = list(init_indicator_parameters);
            elif isinstance(init_indicator_parameters, IndicatorParameter):
                self.__indicator_parameters.append(init_indicator_parameters);
            self.__indicator_parameters.sort();

    def add_indicator_parameter(self, indicator_parameter: IndicatorParameter):
        self.__indicator_parameters.append(indicator_parameter);
        self.__indicator_parameters.sort();

    def push_to_database(self, database_settings: DatabaseSettings):
        if len(self.__indicator_parameters) > 0:
            database = Database_Writer(database_settings=database_settings);
            database.add_table(table_name=self.__coin_symbol);
            for parameter in self.__indicator_parameters:
                timestamp = get_current_timestamp();
                database.add_data(table_name=self.__coin_symbol,
                                  timestamp=timestamp,
                                  tupel_with_data=(timestamp,
                                                   self.__indicator_tree_name,
                                                   parameter.get_identifier_for_database(),
                                                   parameter.get_value()));
            database.close_database();

    def apply_to_tree(self, indicator_tree: ActionNode):
        for parameter in self.__indicator_parameters:
            if not indicator_tree.update_parameter_in_tree_and_reset(indicator_parameter=parameter):
                raise ValueError("Identifier does not fit to indicator tree: " + str(parameter.get_identifier()));
