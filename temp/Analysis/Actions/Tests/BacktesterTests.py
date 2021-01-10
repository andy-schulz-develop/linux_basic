
import unittest;
import decimal;
import logging;
import time;
from pathlib import Path;
from Analysis.DBBacktester import DBBacktester;
from Settings.Markets import unittest_market;
from Tools.LoggerCreator import LoggerCreator;
from Tools.Tests.DatabaseHandlerTests import drop_unittest_table;
from Analysis.Actions.ActionTreeFactory import ActionTreeFactory;
from Tools.HelperFunctions import return_epoch_timestamp, return_human_readable_timestamp;
from Settings.Markets import timestamp_index;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Tools.Database_Handler import Database_Writer, Database_Reader;
from Settings.Database import unittests_write_currency_database_settings, unittests_read_currency_database_settings, \
    unittest_indicator_parameter_database_settings;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class BacktesterTests(ActionTestSuite):

    def test_backtester(self):
        self.clear_trade_manager_factory();
        # Input variables
        coin = "XXXYYY";
        table_name = coin;
        start_time = "2020-04-07 00:32:00";
        step_size = 1000;
        data_start_time = return_epoch_timestamp(start_time) - 500 * step_size;
        data_list = self.get_input_data_scenario3(start_time=data_start_time, step_size=step_size);
        end_time = return_human_readable_timestamp(data_list[-1][timestamp_index]);
        run_name = "run";
        backtester_result_directory = "backtester_results/unittest";
        result_txt_file = backtester_result_directory + "/" + run_name + "_results.txt";
        result_plots_file = backtester_result_directory + "/" + run_name + "_plots.png";
        number_of_lines_in_result_txt_before = self.get_number_of_lines_in_file(result_txt_file);

        # Logger initialization
        logger_name = coin + "_dbbacktester";
        log_file_name = logger_name + ".log";
        log_file_path = "logs/" + log_file_name;
        my_logger = LoggerCreator.createLogger(name=logger_name,
                                               logfile_filename=log_file_name,
                                               log_level=logging.DEBUG);
        number_of_lines_in_log_before = self.get_number_of_lines_in_file(log_file_path);

        # Database preparation
        my_logger.info("Dropping table " + table_name);
        drop_unittest_table(table_name=table_name);
        database_writer = Database_Writer(database_settings=unittests_write_currency_database_settings,
                                          logger_name=logger_name);
        database_writer.add_table(table_name);
        for value in self.convert_for_db(data=data_list):
            database_writer.add_data(table_name=table_name,
                                     timestamp=value[timestamp_index],
                                     tupel_with_data=value);
        database_writer.close_database();
        time.sleep(1);
        database_reader = Database_Reader(database_settings=unittests_read_currency_database_settings);
        self.assertEqual(999,
                         database_reader.count_lines_in_time_range(table_name=table_name,
                                                                   start_time=data_start_time,
                                                                   end_time=None), msg="Database is empty!");
        database_reader.close_database();

        # Actual start of Backtester
        tree_factory = ActionTreeFactory(coin=coin);
        indicator_tree = tree_factory.create_tree_for_backtesting();

        fetcher = DBBacktester(initiation_time_string=start_time,
                               end_time_string=end_time,
                               amount_of_money=100,
                               settings_package=unittest_market,
                               coin=coin,
                               indicator_tree=indicator_tree,
                               run_name=run_name,
                               results_directory=backtester_result_directory);
        fetcher.start_process();
        fetcher.stop_process();
        result = fetcher.get_results();

        backtester_result_directory_path = Path(backtester_result_directory);
        result_text_file_path = Path(result_txt_file);
        result_plots_file_path = Path(result_plots_file);
        log_file_path_path = Path(log_file_path);
        self.assertTrue(backtester_result_directory_path.is_dir());
        self.assertTrue(result_text_file_path.is_file());
        self.assertTrue(result_plots_file_path.is_file());
        self.assertTrue(log_file_path_path.is_file());
        # self.assertEqual(2033, self.get_number_of_lines_in_file(log_file_path) - number_of_lines_in_log_before);
        # self.assertEqual(26, self.get_number_of_lines_in_file(result_txt_file) - number_of_lines_in_result_txt_before);

        result_dict = result.get_result_dict();
        # self.assertIsInstance(result_dict, dict);
        # self.assertEqual(result_dict.get("04-Price change in %"), decimal.Decimal("-50.0"));
        # self.assertEqual(result.get_gain(), decimal.Decimal("-50.09995"));
        # self.assertEqual(result_dict.get("03-Gain in % with less precision transactions"), decimal.Decimal("-50.0995"));

        # Database preparation
        my_logger.info("Dropping table " + table_name);
        drop_unittest_table(table_name=table_name);
        time.sleep(1);
        result.set_indicator_parameters(indicator_parameter_permutation=
                                        ((("buy_limit", ), 1.033), (("sell_limit", ), 0.99)));
        print(str(result.get_indicator_parameters()))
        result.push_indicator_parameters_to_database(database_settings=unittest_indicator_parameter_database_settings);
        another_fetcher = DBBacktester(initiation_time_string=start_time,
                                       end_time_string=end_time,
                                       amount_of_money=100,
                                       settings_package=unittest_market,
                                       coin=coin,
                                       indicator_tree=tree_factory.create_tree_for_backtesting(),
                                       run_name=run_name,
                                       results_directory=backtester_result_directory);
        indicator_tree_from_database = \
            another_fetcher.build_tree_from_database(database_settings=unittest_indicator_parameter_database_settings);
        print(str(indicator_tree_from_database.get_all_tree_parameters()));
        indicator_tree_from_database.print_tree_definition();


if __name__ == '__main__':
    unittest.main()
