import unittest;
import decimal;
from Analysis.Actions.TradeManager import MarketOperation;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Analysis.Actions.WorldFormula import WorldFormula;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class WorldFormulaIndicatorTests(ActionTestSuite):

    def test_warm_ups(self):
        insufficient_warm_up_data = self.generate_input_data(number_of_steps=5, value=decimal.Decimal("100.0"));
        sufficient_warm_up_data = self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"));

        indicator = WorldFormula(oversold_node=self._buy_action,
                                 overbought_node=self._sell_action,
                                 default_node=self._default_action,
                                 buy_in_limit=1.02,
                                 sell_limit=0.99);

        self.set_unittest_trade_manager(last_operation=MarketOperation.sell,
                                        last_transaction_time=1,
                                        last_transaction_price=decimal.Decimal("100.0"));
        self.failed_warm_up(indicator=indicator, insufficient_warm_up_data=insufficient_warm_up_data);
        self.successful_warm_up(indicator=indicator, sufficient_warm_up_data=sufficient_warm_up_data);

    def test_entire_run(self):
        warm_up_data = self.generate_input_data(number_of_steps=20, value=decimal.Decimal("5.0"));
        self.set_unittest_trade_manager(last_operation=MarketOperation.sell,
                                        last_transaction_time=1,
                                        last_transaction_price=decimal.Decimal("5.0"));

        indicator = WorldFormula(oversold_node=self._buy_action,
                                 overbought_node=self._sell_action,
                                 default_node=self._default_action,
                                 buy_in_limit=1.02,
                                 sell_limit=0.99);
        self.run_csv_data(indicator=indicator,
                          sufficient_warm_up_data=warm_up_data,
                          parameter_names=["sell_limit", "buy_limit"],
                          data_source_file="Analysis/Actions/Tests/Testdata/WorldFormulaTestData.csv");
        indicator.shutdown_indicator();


if __name__ == '__main__':
    unittest.main()
