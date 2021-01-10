
import unittest;
import decimal;
import pandas;
from timeit import default_timer as timer;
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Settings.Markets import primary_value_index, timestamp_index;
from Analysis.Actions.TradeManager import TradeManager, MarketOperation;
from Analysis.Actions.TradeManagerFactory import trade_manager_factory;
from Analysis.Actions.BuySellActions import Buy, Sell;


class UnitTestAction(ActionNode):

    def __init__(self, identifier, default_node=None):
        """
        Constructor
        """
        super(UnitTestAction, self).__init__(default_node=default_node);
        self.__identifier = identifier;

    def get_identifier(self):
        return self.__identifier;

    def check(self, data_array: list):
        return self._children.get(ChildrenNames.default_branch);


class UnitTestTradeManager(TradeManager):
    """
    class docs
    """

    def __init__(self,
                 last_operation,
                 last_transaction_price,
                 last_transaction_time):
        """
        Constructor
        """
        super(UnitTestTradeManager, self).__init__();
        self._last_operation = last_operation;
        self._last_transaction_price = last_transaction_price;
        self._last_transaction_time = last_transaction_time;

    def set_last_operation(self, operation: MarketOperation):
        self._last_operation = operation;

    def set_last_transaction_price(self, transaction_price: decimal.Decimal):
        self._last_transaction_price = transaction_price;

    def set_last_transaction_time(self, transaction_time: int):
        self._last_transaction_time = transaction_time;

    def set_sell_is_possible(self, sell_is_possible: bool):
        self._sell_is_possible = sell_is_possible;

    def buy(self, data_array: list):
        self._last_operation = MarketOperation.buy;
        self._last_transaction_time = data_array[-1][timestamp_index];
        self._last_transaction_price = data_array[-1][primary_value_index];

    def sell(self, data_array: list):
        self._last_operation = MarketOperation.sell;
        self._last_transaction_time = data_array[-1][timestamp_index];
        self._last_transaction_price = data_array[-1][primary_value_index];


class ActionTestSuite(unittest.TestCase):

    _buy_action = Buy(coin_symbol="UNTTST", default_node=UnitTestAction(identifier=1));
    _sell_action = Sell(coin_symbol="UNTTST", default_node=UnitTestAction(identifier=-1));
    _default_action = UnitTestAction(identifier=0, default_node=UnitTestAction(identifier=0));
    _trade_manager = None;

    def failed_warm_up(self, indicator, insufficient_warm_up_data):
        if self._trade_manager is None:
            self.set_unittest_trade_manager();
        self.assertFalse(indicator.init_indicator(data_array=insufficient_warm_up_data));

    def successful_warm_up(self, indicator, sufficient_warm_up_data):
        if self._trade_manager is None:
            self.set_unittest_trade_manager();
        self.assertTrue(indicator.init_indicator(data_array=sufficient_warm_up_data));

    def init_and_run_generated_data(self,
                                    indicator,
                                    sufficient_warm_up_data,
                                    input_data,
                                    calculation_results,
                                    action_nodes):
        self.assertTrue(indicator.init_indicator(data_array=sufficient_warm_up_data));
        self.run_generated_data(indicator, sufficient_warm_up_data, input_data, calculation_results, action_nodes);

    def run_generated_data(self, indicator, sufficient_warm_up_data, input_data, calculation_results, action_nodes):
        for i in range(0, len(input_data)):
            sufficient_warm_up_data.append(input_data[i]);
            result = indicator.check(data_array=sufficient_warm_up_data);
            self.assertAlmostEqual(indicator.get_calculation_result(), calculation_results[i]);
            self.assertIs(result, action_nodes[i]);

    def run_csv_data(self,
                     indicator: ActionNode,
                     sufficient_warm_up_data: list,
                     parameter_names: list,
                     data_source_file: str):
        data_frame = pandas.read_csv(data_source_file);
        for key in parameter_names:
            indicator.update_parameter_in_tree_and_reset(identifier=(key, ), value=data_frame[key][0]);
        self.successful_warm_up(indicator=indicator, sufficient_warm_up_data=sufficient_warm_up_data);

        # Rough performance check - Start
        number_of_data_points = 0;
        start = timer();
        # Actual run
        for index, row in data_frame.iterrows():
            number_of_data_points += 1;
            sufficient_warm_up_data.append(
                self.convert_to_data_point(timestamp=row["time_stamps"], price=row["prices"]));
            result_action = indicator.check(data_array=sufficient_warm_up_data);
            result = result_action.check(data_array=sufficient_warm_up_data);
            self.assertAlmostEqual(indicator.get_calculation_result(),
                                   decimal.Decimal(row["calculation_results"]),
                                   msg="Deviation at timestamp " + str(row["time_stamps"]));  # , places=4
            self.assertEqual(result.get_identifier(), int(row["action_nodes"]),
                             msg="Deviation at timestamp " + str(row["time_stamps"]));
        # Rough performance check - End
        end = timer();
        self.assertLess((end - start) / float(number_of_data_points), 0.5,
                        msg="Calculation takes too much time!!");

    @staticmethod
    def convert_to_data_point(timestamp: int, price) -> tuple:
        temp_decimals = [decimal.Decimal("0.0")] * 14;
        temp_integers = [0] * 6;
        point = temp_decimals + temp_integers;
        point[primary_value_index] = decimal.Decimal(price);
        point[timestamp_index] = timestamp;
        return tuple(point);

    def generate_input_data(self, number_of_steps: int, value: float, start_time: int = 0, step_size: int = 1) -> list:
        input_data_list = [];
        for time in range(start_time, number_of_steps * step_size + start_time, step_size):
            input_data_list.append(self.convert_to_data_point(timestamp=time, price=value));
        return input_data_list;

    def get_input_data_scenario1(self) -> list:
        """
        :return: list
                           _____
         _____       _____|
        |     |_____|
        """
        input_data = self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"));
        input_data += self.generate_input_data(number_of_steps=100, value=decimal.Decimal("50.0"), start_time=100);
        input_data += self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"), start_time=200);
        input_data += self.generate_input_data(number_of_steps=100, value=decimal.Decimal("150.0"), start_time=300);
        return input_data;

    def get_input_data_scenario2(self, step_size=1000) -> list:
        """
        :return: list
                                         _______
         __________           __________|
        |         |__________|
        """
        input_data = self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"), step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=100, value=decimal.Decimal("50.0"),
                                               start_time=100 * step_size, step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"),
                                               start_time=200 * step_size, step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=100, value=decimal.Decimal("150.0"),
                                               start_time=300 * step_size, step_size=step_size);
        return input_data;

    def get_input_data_scenario3(self, step_size=1000, start_time=1587717653000) -> list:
        """
        :return: list
                                         _______
         __________           __________|      |__________
        |         |__________|
        """
        input_data = self.generate_input_data(number_of_steps=200,
                                              value=decimal.Decimal("100.0"),
                                              start_time=start_time,
                                              step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=200,
                                               value=decimal.Decimal("50.0"),
                                               start_time=input_data[-1][timestamp_index] + step_size,
                                               step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=200,
                                               value=decimal.Decimal("100.0"),
                                               start_time=input_data[-1][timestamp_index] + step_size,
                                               step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=200,
                                               value=decimal.Decimal("150.0"),
                                               start_time=input_data[-1][timestamp_index] + step_size,
                                               step_size=step_size);
        input_data += self.generate_input_data(number_of_steps=200,
                                               value=decimal.Decimal("50.0"),
                                               start_time=input_data[-1][timestamp_index] + step_size,
                                               step_size=step_size);
        return input_data;

    def set_unittest_trade_manager(self,
                                   last_operation: MarketOperation = MarketOperation.sell,
                                   last_transaction_price: decimal.Decimal = decimal.Decimal("1.0"),
                                   last_transaction_time: int = 1):
        self._trade_manager = UnitTestTradeManager(last_operation=last_operation,
                                                   last_transaction_price=last_transaction_price,
                                                   last_transaction_time=last_transaction_time)
        trade_manager_factory.set_trade_manager(key="UnitTestTradeManager", trade_manager=self._trade_manager);

    def set_general_trade_manager(self, key: str, trade_manager: TradeManager):
        self._trade_manager = trade_manager;
        trade_manager_factory.clear_trade_managers();
        trade_manager_factory.set_trade_manager(key=key, trade_manager=trade_manager);
        comparing_trade_manager = trade_manager_factory.get_current_trade_manager();
        self.assertIs(trade_manager, comparing_trade_manager);

    @staticmethod
    def clear_trade_manager_factory():
        trade_manager_factory.clear_trade_managers();

    @staticmethod
    def get_number_of_lines_in_file(file_name: str):
        try:
            with open(file_name) as file_handler:
                result = len(file_handler.readlines());
            return result
        except FileNotFoundError:
            return 0;

    @staticmethod
    def convert_for_db(data: list):
        new_data_list = [];
        for element in data:
            new_element = [];
            for element_entry in element:
                if isinstance(element_entry, decimal.Decimal):
                    new_element.append(float(element_entry));
                else:
                    new_element.append(element_entry);
            new_data_list.append(tuple(new_element));
        return new_data_list;
