"""
Created on Sep 02, 2019

@author: me
"""
from Analysis.MultiBacktester import MultiBacktester;
from Tools.HelperFunctions import get_current_timestamp;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;
from Analysis.Actions.BacktesterStatistics import BacktesterResults;


class ManualMultiBacktester(MultiBacktester):
    """
    ManualMultiBacktester
    """

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 initiation_time_string: str,
                 end_time_string=None,
                 run_name: str = "",
                 amount_of_money=100,
                 results_directory: str = "backtester_results",
                 verbose_print_and_plot: bool = True):
        """
        Constructor
        """
        super(ManualMultiBacktester, self).__init__(settings_package=settings_package,
                                                    coin=coin,
                                                    indicator_tree=indicator_tree,
                                                    initiation_time_string=initiation_time_string,
                                                    end_time_string=end_time_string,
                                                    run_name=run_name,
                                                    amount_of_money=amount_of_money,
                                                    results_directory=results_directory,
                                                    verbose_print_and_plot=verbose_print_and_plot);
        self.__total_number_of_runs = 1;

    def _post_processing(self, backtester_result: BacktesterResults):
        self._list_of_results.append(backtester_result);
        approx_remaining_time_in_sec = \
            (self.__total_number_of_runs - self._run_number) * self._average_processing_time_per_run + 6;
        # +6 for more accuracy
        hours, seconds = divmod(approx_remaining_time_in_sec, 3600);  # split to hours and seconds
        minutes, seconds = divmod(seconds, 60);  # split the seconds to minutes and seconds
        remaining_time = "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds);
        print("Run No. " + str(self._run_number) + " of " + str(self.__total_number_of_runs) +
              " finished. Remaining time: " + remaining_time);
        return backtester_result;

    def start_process(self):
        print("Starting first run");
        self._start_time = get_current_timestamp();
        self.__total_number_of_runs = 1;
        for key, values in self._indicator_parameters.items():
            self.__total_number_of_runs *= len(values);
        self.run_over_all_permutations();

        self._plot_summary();

        print("Best run: ");
        self._best_result_of_all_runs.print_results_to_screen();
        return self._best_result_of_all_runs;
