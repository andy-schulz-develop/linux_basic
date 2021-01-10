"""
Created on Apr 28, 2018

@author: me
"""
from Analysis.Backtester import Backtester;
from decimal import Decimal;
import csv;
from Tools.HelperFunctions import get_current_timestamp;
from Settings.Markets import timestamp_index, primary_value_index;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;


class CsvBacktester(Backtester):
    """
    classdocs
    """
    __progress = 0.0;

    def __init__(self,
                 file_name: str,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 name_of_target_indicator_node=None,
                 indicator_parameters=None,
                 run_name: str = "",
                 amount_of_money=100,
                 results_directory: str = "backtester_results",
                 print_and_plot=True):
        """
        Constructor
        """
        super(CsvBacktester, self).__init__(settings_package=settings_package,
                                            coin=coin,
                                            indicator_tree=indicator_tree,
                                            initiation_time_string="2019-07-28 22:00:00",
                                            end_time_string=None,
                                            name_of_target_indicator_node=name_of_target_indicator_node,
                                            indicator_parameters=indicator_parameters,
                                            run_name=run_name,
                                            amount_of_money=amount_of_money,
                                            results_directory=results_directory,
                                            print_and_plot=print_and_plot);
        self.__file_name = file_name;

    @staticmethod
    def convert(list_of_strings):
        return (Decimal(list_of_strings[1]), Decimal(list_of_strings[2]), Decimal(list_of_strings[3]),
                Decimal(list_of_strings[4]), Decimal(list_of_strings[5]), Decimal(list_of_strings[6]),
                Decimal(list_of_strings[7]), Decimal(list_of_strings[8]), Decimal(list_of_strings[9]),
                Decimal(list_of_strings[10]), Decimal(list_of_strings[11]), Decimal(list_of_strings[12]),
                Decimal(list_of_strings[13]), Decimal(list_of_strings[14]), Decimal(list_of_strings[15]),
                int(float(list_of_strings[16])), int(float(list_of_strings[17])), int(float(list_of_strings[18])),
                int(float(list_of_strings[19])), int(float(list_of_strings[20])));

    def start_process(self):
        initialization_complete = False;
        """
        Reads csv file that is created by this command:
        sudo mysqldump binance ETHBTC --fields-terminated-by ','  --fields-enclosed-by '"' \
        --fields-escaped-by '\'  --no-create-info --tab /var/lib/mysql/folder/
        Maybe parameter "-u <user> -p" is required.
        :return: Calls evaluation function and returns result dictionary
        """
        self._mylogger.info("Loading data from csv file '" + self.__file_name + "'");
        total_number_of_data_points = sum(1 for line in open(self.__file_name));
        started_at = get_current_timestamp();
        self._mylogger.info("Loaded file with " + str(total_number_of_data_points) + " lines.");
        with open(self.__file_name, newline='') as csv_file:
            data_reader = csv.reader(csv_file, delimiter=',', quotechar='"');
            for row in data_reader:
                data_point = self.convert(row);
                self._trade_manager.init_values(first_timestamp=data_point[timestamp_index],
                                                first_price=data_point[primary_value_index],
                                                started_at=started_at,
                                                total_number_of_data_points=total_number_of_data_points);
                if initialization_complete:
                    self._process_data_point(data_point=data_point);
                else:
                    self._data.append(data_point);
                    initialization_complete = self._indicator_tree.init_indicator(self._data);
        self._mylogger.info("Finished analysis");
        # If initialization was not finished return None
        if initialization_complete:
            return self.finish();
        else:
            self._mylogger.warning("Indicators did not initialize. Data set does not contain enough " +
                                   "data points or does not cover a large enough time span.")
            return None;
