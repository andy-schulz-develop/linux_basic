"""
Created on Apr 28, 2018

@author: me
"""
import gc;
from Analysis.Backtester import Backtester;
from Settings.Markets import timestamp_index;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;


class DBBacktester(Backtester):
    """
    class docs
    """
    __progress = 0.0;

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 initiation_time_string,
                 end_time_string=None,
                 run_name: str = "",
                 amount_of_money=100,
                 results_directory: str = "backtester_results",
                 parameter_definitions: list = None,
                 print_and_plot: bool = True):
        """
        Constructor
        """
        super(DBBacktester, self).__init__(settings_package=settings_package,
                                           coin=coin,
                                           indicator_tree=indicator_tree,
                                           initiation_time_string=initiation_time_string,
                                           end_time_string=end_time_string,
                                           run_name=run_name,
                                           amount_of_money=amount_of_money,
                                           results_directory=results_directory,
                                           parameter_definitions=parameter_definitions,
                                           print_and_plot=print_and_plot);
        self.__database_settings = settings_package.get_analyzer_database_settings();

    def start_process(self):
        self._init_data_for_timestamp(timestamp=self._start_time);
        temp_start_time = self._data[-1][timestamp_index];
        reached_end_of_interval = False;
        while not reached_end_of_interval:
            data, reached_end_of_interval, total_number_of_data_points =\
                self._fetch_from_database(begin=temp_start_time, end=self._end_time);
            temp_start_time = data[-1][timestamp_index];
            for data_point in data:
                self._add_data_to_list(data_point);
            data.clear();
            gc.collect();
