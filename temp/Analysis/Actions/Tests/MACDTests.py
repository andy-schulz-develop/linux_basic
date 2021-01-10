import unittest;
import decimal;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Analysis.Actions.MACD_Indicator import MACDIndicator;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class MACDTests(ActionTestSuite):

    def test_warm_ups(self):
        insufficient_warm_up_data = self.generate_input_data(number_of_steps=5, value=decimal.Decimal("100.0"));
        sufficient_warm_up_data = self.generate_input_data(number_of_steps=70, value=decimal.Decimal("100.0"));

        indicator = MACDIndicator(oversold_node=self._buy_action,
                                  overbought_node=self._sell_action,
                                  default_node=self._default_action,
                                  macd_ema_time_interval=3,
                                  slow_ema_time_interval=5,
                                  fast_ema_time_interval=2);
        self.failed_warm_up(indicator=indicator, insufficient_warm_up_data=insufficient_warm_up_data);
        self.successful_warm_up(indicator=indicator, sufficient_warm_up_data=sufficient_warm_up_data);

    def test_entire_run(self):
        warm_up_data = self.generate_input_data(number_of_steps=1000, value=decimal.Decimal("100.0"));

        indicator = MACDIndicator(oversold_node=self._buy_action,
                                  overbought_node=self._sell_action,
                                  default_node=self._default_action,
                                  macd_ema_time_interval=10,
                                  slow_ema_time_interval=70,
                                  fast_ema_time_interval=26);
        self.run_csv_data(indicator=indicator,
                          sufficient_warm_up_data=warm_up_data,
                          parameter_names=["macd_ema", "slow_ema", "fast_ema"],
                          data_source_file="Analysis/Actions/Tests/Testdata/MACDTestData.csv");


if __name__ == '__main__':
    unittest.main()
