import unittest;
import decimal;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Analysis.Actions.TrendIndicator import TrendIndicator;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class TrendIndicatorTests(ActionTestSuite):

    def test_warm_ups(self):
        insufficient_warm_up_data = self.generate_input_data(number_of_steps=5, value=decimal.Decimal("100.0"));
        sufficient_warm_up_data = self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"));

        indicator = TrendIndicator(upward_trend_node=self._buy_action,
                                   downward_trend_node=self._sell_action,
                                   default_node=self._default_action,
                                   time_interval=10);
        self.failed_warm_up(indicator=indicator, insufficient_warm_up_data=insufficient_warm_up_data);
        self.successful_warm_up(indicator=indicator, sufficient_warm_up_data=sufficient_warm_up_data);

    def test_entire_run(self):
        warm_up_data = self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"));
        input_data = self.get_input_data_scenario1();

        indicator = TrendIndicator(upward_trend_node=self._buy_action,
                                   downward_trend_node=self._sell_action,
                                   default_node=self._default_action,
                                   time_interval=10);
        calculation_results = [decimal.Decimal("0.0")] * 100 + [decimal.Decimal("-0.05")] * 10 + \
                              [decimal.Decimal("0.0")] * 90 + [decimal.Decimal("0.1")] * 10 + \
                              [decimal.Decimal("0.0")] * 90 + [decimal.Decimal("0.05")] * 10 + \
                              [decimal.Decimal("0.0")] * 90;
        action_nodes = [self._default_action] * 100 + [self._sell_action] * 10 + [self._default_action] * 90 + \
                       [self._buy_action] * 10 + [self._default_action] * 90 + [self._buy_action] * 10 + \
                       [self._default_action] * 90;

        self.init_and_run_generated_data(indicator=indicator,
                                         sufficient_warm_up_data=warm_up_data,
                                         input_data=input_data,
                                         calculation_results=calculation_results,
                                         action_nodes=action_nodes);
        indicator.shutdown_indicator();


if __name__ == '__main__':
    unittest.main()
