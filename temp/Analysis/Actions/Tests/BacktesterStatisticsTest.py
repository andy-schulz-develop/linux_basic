import unittest;
import decimal;
import time;
from Tools.HelperFunctions import get_current_timestamp;
from Settings.Markets import primary_value_index, timestamp_index;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Analysis.Actions.BacktesterStatistics import BacktesterResults, BacktesterStatistics, BacktesterAction;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class BacktesterStatisticsTest(ActionTestSuite):

    @staticmethod
    def create_backtester_results(gain: decimal.Decimal):
        result = BacktesterResults(
            coin_symbol="ETHBTC",
            start_time=get_current_timestamp(),
            amount_of_money=decimal.Decimal("100.0"),
            end_time=get_current_timestamp() + 5000,
            run_name="UnittestRun",
            results_file_name="UnittestFile",
            plots_file_name="UnittestPlot");
        result.init_values(first_timestamp=get_current_timestamp(),
                           first_price=decimal.Decimal("5.0"),  # input_data[0][primary_value_index],
                           indicator_tree_information="_name: empty_indicator\nany_limit: decimal.Decimal(5.0)",
                           indicator_tree_name="empty_indicator");
        result.set_results(latest_timestamp=get_current_timestamp(),
                           latest_price=decimal.Decimal("10.0"),
                           fiat_currency=decimal.Decimal("100.0") + gain,
                           crypto_currency=decimal.Decimal("0.0"),
                           number_of_buys=5,
                           number_of_sells=5,
                           variance_of_price=decimal.Decimal("1.0"),
                           variance_of_price_derivative=decimal.Decimal("0.1"),
                           fiat_currency_w_less_precision=decimal.Decimal("20.0"),
                           crypto_currency_w_less_precision=decimal.Decimal("110.0"),
                           total_number_of_data_points=400);
        return result;

    def test_just_backtester_result(self):
        wait_time = 2.0;

        result = BacktesterResults(
            coin_symbol="ETHBTC",
            start_time=get_current_timestamp(),
            amount_of_money=decimal.Decimal("100.0"),
            end_time=get_current_timestamp() + 5000,
            run_name="UnittestRun",
            results_file_name="UnittestFile",
            plots_file_name="UnittestPlot");
        result.init_values(first_timestamp=get_current_timestamp(),
                           first_price=decimal.Decimal("5.0"),  # input_data[0][primary_value_index],
                           indicator_tree_information="_name: empty_indicator\nany_limit: decimal.Decimal(5.0)",
                           indicator_tree_name="empty_indicator");
        time.sleep(wait_time);
        result.set_results(latest_timestamp=get_current_timestamp(),
                           latest_price=decimal.Decimal("10.0"),
                           fiat_currency=decimal.Decimal("100.0"),
                           crypto_currency=decimal.Decimal("2.0"),
                           number_of_buys=5,
                           number_of_sells=5,
                           variance_of_price=decimal.Decimal("1.0"),
                           variance_of_price_derivative=decimal.Decimal("0.1"),
                           fiat_currency_w_less_precision=decimal.Decimal("20.0"),
                           crypto_currency_w_less_precision=decimal.Decimal("110.0"),
                           total_number_of_data_points=400);
        result_dict = result.get_result_dict();
        self.assertIsInstance(result_dict, dict);
        self.assertAlmostEqual(result_dict.get("12-Time needed in sec"), wait_time, places=1);
        self.assertEqual(result_dict.get("02-Gain in %"), decimal.Decimal("20.0"));
        self.assertEqual(result.get_gain(), decimal.Decimal("20.0"));
        self.assertEqual(result_dict.get("04-Price change in %"), decimal.Decimal("100.0"));

    def test_sort_max_min_of_backtester_result(self):
        list_of_backtester_results = [];
        for i in range(9, -1, -1):
            list_of_backtester_results.append(self.create_backtester_results(gain=decimal.Decimal(i * 10)));
        self.assertEqual(list_of_backtester_results[0].get_gain(), decimal.Decimal("90.0"));
        self.assertEqual(list_of_backtester_results[-1].get_gain(), decimal.Decimal("0.0"));
        sorted_list_of_backtester_results = sorted(list_of_backtester_results);
        self.assertEqual(sorted_list_of_backtester_results[0].get_gain(), decimal.Decimal("0.0"));
        self.assertEqual(sorted_list_of_backtester_results[-1].get_gain(), decimal.Decimal("90.0"));

        best_result = max(list_of_backtester_results);
        self.assertEqual(best_result.get_gain(), decimal.Decimal("90.0"));
        worst_result = min(list_of_backtester_results);
        self.assertEqual(worst_result.get_gain(), decimal.Decimal("0.0"));

    def test_backtester_statistics(self):
        input_data = self.get_input_data_scenario2();
        start_time = get_current_timestamp();
        indicator_name = "empty_indicator";

        statistics = BacktesterStatistics(
            coin_symbol="ETHBTC",
            start_time=get_current_timestamp(),
            amount_of_money=decimal.Decimal("100.0"),
            end_time=get_current_timestamp() + 5000,
            run_name="UnittestRun",
            results_directory="backtester_results/unittest/");

        i = 20;
        statistics.init_values(first_timestamp=input_data[0][timestamp_index],
                               first_price=input_data[0][primary_value_index],
                               indicator_tree_information="_name: empty_indicator\nany_limit: decimal.Decimal(5.0)",
                               indicator_tree_name=indicator_name,
                               last_timestamp=input_data[i-1][timestamp_index],
                               last_price=input_data[i-1][primary_value_index]);

        while i < 150:
            data_point = input_data[i];
            statistics.collect_values(latest_timestamp=data_point[timestamp_index],
                                      latest_price=data_point[primary_value_index],
                                      calculation_result=decimal.Decimal("1.0"),
                                      process_start_time=start_time);
            i += 1;
        statistics.buy(input_data[:i+1]);
        while i < 300:
            data_point = input_data[i];
            statistics.collect_values(latest_timestamp=data_point[timestamp_index],
                                      latest_price=data_point[primary_value_index],
                                      calculation_result=decimal.Decimal("2.0"),
                                      process_start_time=start_time);
            i += 1;
        statistics.sell(input_data[:i+1]);
        while i < len(input_data):
            data_point = input_data[i];
            statistics.collect_values(latest_timestamp=data_point[timestamp_index],
                                      latest_price=data_point[primary_value_index],
                                      calculation_result=decimal.Decimal("3.0"),
                                      process_start_time=start_time);
            i += 1;
        result = statistics.print_and_plot_results();
        result_dict = result.get_result_dict();
        self.assertIsInstance(result_dict, dict);
        self.assertEqual(result_dict.get("04-Price change in %"), decimal.Decimal("50.0"));
        self.assertEqual(result_dict.get("18-Indicator tree name"), indicator_name);
        self.assertEqual(result.get_gain(), decimal.Decimal("199.4003"));
        self.assertEqual(result_dict.get("03-Gain in % with less precision transactions"), decimal.Decimal("199.4015"));

    def test_backtester_action_warm_ups(self):
        insufficient_warm_up_data = self.generate_input_data(number_of_steps=5, value=decimal.Decimal("100.0"));
        sufficient_warm_up_data = self.generate_input_data(number_of_steps=100, value=decimal.Decimal("100.0"));

        test_candidate = BacktesterAction(default_node=self._default_action, analysis_node=self._default_action);

        self.failed_warm_up(indicator=test_candidate, insufficient_warm_up_data=insufficient_warm_up_data);
        self.successful_warm_up(indicator=test_candidate, sufficient_warm_up_data=sufficient_warm_up_data);

    def test_backtester_action_statistic(self):
        input_data = self.get_input_data_scenario2();
        calculation_results = [decimal.Decimal("0.0")] * len(input_data);
        action_nodes = [self._default_action] * len(input_data);

        statistics = BacktesterStatistics(
            coin_symbol="ETHBTC",
            start_time=get_current_timestamp(),
            amount_of_money=decimal.Decimal("100.0"),
            end_time=get_current_timestamp() + 5000,
            run_name="UnittestRun",
            results_directory="backtester_results/unittest/");
        self.set_general_trade_manager(key="backtester_statistics", trade_manager=statistics);

        test_candidate = BacktesterAction(default_node=self._default_action, analysis_node=self._default_action);

        i = 150;
        self.init_and_run_generated_data(indicator=test_candidate,
                                         sufficient_warm_up_data=input_data[:i],
                                         input_data=input_data[:i],
                                         calculation_results=calculation_results,
                                         action_nodes=action_nodes);
        statistics.buy(input_data[:i+1]);
        j = i;
        i = 300;
        self.run_generated_data(indicator=test_candidate,
                                sufficient_warm_up_data=input_data[:j],
                                input_data=input_data[j:i],
                                calculation_results=calculation_results[j:],
                                action_nodes=action_nodes[j:]);
        statistics.sell(input_data[:i+1]);
        self.run_generated_data(indicator=test_candidate,
                                sufficient_warm_up_data=input_data[:i],
                                input_data=input_data[i:],
                                calculation_results=calculation_results[i:],
                                action_nodes=action_nodes[i:]);
        test_candidate.shutdown_indicator();
        result = statistics.get_results();
        result_dict = result.get_result_dict();
        self.assertIsInstance(result_dict, dict);
        self.assertEqual(result_dict.get("04-Price change in %"), decimal.Decimal("50.0"));
        self.assertEqual(result.get_gain(), decimal.Decimal("199.4003"));
        self.assertEqual(result_dict.get("03-Gain in % with less precision transactions"), decimal.Decimal("199.4015"));


if __name__ == '__main__':
    unittest.main()
