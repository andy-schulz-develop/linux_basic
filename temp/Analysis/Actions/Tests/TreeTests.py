import unittest;
import decimal;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Analysis.Actions.WorldFormula import WorldFormula;
from Analysis.Actions.Stop_Loss_Indicator import Stop_Loss_Indicator;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class TreeTests(ActionTestSuite):

    def create_tree(self):
        world_formula = WorldFormula(oversold_node=self._buy_action,
                                     overbought_node=self._sell_action,
                                     default_node=None,
                                     buy_in_limit=1.029,
                                     sell_limit=0.97);
        stop_loss_indicator = Stop_Loss_Indicator(time_interval=100000,
                                                  stop_node=self._sell_action,
                                                  default_node=world_formula,
                                                  stop_loss_limit=0.992);
        return stop_loss_indicator;

    def test_warm_ups(self):
        insufficient_warm_up_data = self.generate_input_data(number_of_steps=5, value=decimal.Decimal("100.0"));
        sufficient_warm_up_data = self.generate_input_data(number_of_steps=70, value=decimal.Decimal("100.0"));

        test_candidate = self.create_tree();

        self.failed_warm_up(indicator=test_candidate, insufficient_warm_up_data=insufficient_warm_up_data);
        self.successful_warm_up(indicator=test_candidate, sufficient_warm_up_data=sufficient_warm_up_data);

    def test_entire_run(self):
        warm_up_data = self.generate_input_data(number_of_steps=1000, value=decimal.Decimal("100.0"));

        test_candidate = self.create_tree();

        self.run_csv_data(indicator=test_candidate,
                          sufficient_warm_up_data=warm_up_data,
                          parameter_names=[],
                          data_source_file="Analysis/Actions/Tests/Testdata/MACDTestData.csv");
        self.run_csv_data(indicator=test_candidate,
                          sufficient_warm_up_data=warm_up_data,
                          parameter_names=[],
                          data_source_file="Analysis/Actions/Tests/Testdata/MACDTestData.csv");


if __name__ == '__main__':
    unittest.main()
