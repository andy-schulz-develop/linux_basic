
import unittest;
import logging;
import time;
import os;
import shutil;
from pathlib import Path;
from Settings.Markets import unittest_market;
from Tools.LoggerCreator import LoggerCreator;
from Tools.Tests.DatabaseHandlerTests import drop_unittest_table;
from Tools.HelperFunctions import return_epoch_timestamp;
from Settings.Markets import timestamp_index;
from Analysis.Actions.Tests.ActionTestSuite import ActionTestSuite;
from Tools.Database_Handler import Database_Writer, Database_Reader;
from Settings.Database import unittests_write_currency_database_settings, unittests_read_currency_database_settings;
from Analysis.CollectionBacktester import run_csv_data;


"""
Execution in console:
python3 -m unittest Tools/Tests/Queue_Handler_Tests.py
"""


class CollectionBacktesterTests(ActionTestSuite):

    def test_collection_backtester(self):
        self.clear_trade_manager_factory();
        # Input variables - Make sure they are compatible with Testdata/CollectionBacktesterTestInput.csv
        coin = "XXXYYY";
        table_name = coin;
        start_time = "2020-03-24 00:32:00";
        step_size = 500000;
        data_start_time = return_epoch_timestamp(start_time) - 350 * step_size;
        data_list = self.get_input_data_scenario3(start_time=data_start_time, step_size=step_size);
        output_directory = "backtester_results/unittest/CollectionBacktesterTests";

        # Cleaning up files and directories
        if os.path.exists(output_directory):
            shutil.rmtree(output_directory);

        # Logger initialization
        logger_name = coin + "_collection_backtester";
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
        run_csv_data(data_source_file="Analysis/Actions/Tests/Testdata/CollectionBacktesterTestInput.csv",
                     market=unittest_market, send_mail=False);

        # Checking if directory exists
        directory_path = Path(output_directory);
        self.assertTrue(directory_path.is_dir(), msg="Directory '" + output_directory + "' was not created!");

        target_results_source = "Analysis/Actions/Tests/Testdata/CollectionBacktesterTestOutput";
        for dirName, subdirList, fileList in os.walk(target_results_source):
            for file_name in fileList:
                target_result_file_name = os.path.join(dirName, file_name);
                output_file_name = os.path.join(output_directory,
                                                os.path.relpath(dirName, target_results_source),
                                                file_name);
                output_file = Path(output_file_name);
                self.assertTrue(output_file.is_file(), msg="File '" + output_file_name + "' was not created!");
                # Compare number of lines in .csv and .txt files
                if output_file_name.endswith(".csv") or output_file_name.endswith(".txt"):
                    self.assertEqual(self.get_number_of_lines_in_file(output_file_name),
                                     self.get_number_of_lines_in_file(target_result_file_name),
                                     msg="File content seems wrong. Wrong file: " + output_file_name);

        # Checking if the log has the right amount of lines in it
        self.assertEqual(1020, self.get_number_of_lines_in_file(log_file_path) - number_of_lines_in_log_before,
                         msg="Log file is missing information.");


if __name__ == '__main__':
    unittest.main()
