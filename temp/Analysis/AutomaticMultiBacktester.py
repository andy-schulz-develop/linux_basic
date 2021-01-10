"""
Created on Sep 02, 2019

@author: me
"""
from Analysis.MultiBacktester import MultiBacktester;
import decimal;


class AutomaticMultiBacktester(MultiBacktester):
    """
    classdocs
    """

    def __init__(self,
                 name_of_target_indicator_node,
                 settings_package,
                 coin,
                 indicator_tree,
                 initiation_time_string,
                 end_time_string=None,
                 run_name="",
                 amount_of_money=100,
                 results_directory="backtester_results"):
        """
        Constructor
        """
        super(AutomaticMultiBacktester, self).__init__(name_of_target_indicator_node=name_of_target_indicator_node,
                                                       settings_package=settings_package,
                                                       coin=coin,
                                                       indicator_tree=indicator_tree,
                                                       initiation_time_string=initiation_time_string,
                                                       end_time_string=end_time_string,
                                                       run_name=run_name,
                                                       amount_of_money=amount_of_money,
                                                       results_directory=results_directory);
        # self.__gain_precision = decimal.Decimal(0.001);
        self.__min_search_interval = decimal.Decimal(0.002);
        self._print_and_plot_in_backtester = False;
        self.__result_table_file_name = self._default_file_name_prefix + "_results_table.csv";

    def _backtester_wrapper(self):
        results_of_single_run = self._run_backtester();
        self.write_results_into_csv_file(results_of_single_run, self.__result_table_file_name);
        print("Run No. " + str(self._run_number) + " finished.");
        return results_of_single_run;

    def start_process(self):
        super(AutomaticMultiBacktester, self).start_process();
        previous_gain = decimal.Decimal(-99999.009);
        gain = previous_gain + self.__min_search_interval + decimal.Decimal(1.0);
        self.__min_search_interval *= self._all_parameter_lists[self._parameter_names[0]][0];
        current_range = self._all_parameter_lists[self._parameter_names[0]][-1] -\
                        self._all_parameter_lists[self._parameter_names[0]][0];
        # TODO: Check if additional interval condition required (see below)
        while current_range > self.__min_search_interval:
            # while abs(gain - previous_gain) > self.__gain_precision:
            self._iterate_over_parameter_lists();
            previous_gain = gain;
            gain = self._best_result_of_all_runs["Gain in %"];
            best_parameters = self._best_result_of_all_runs["Indicator parameters"];
            print("Maximum gain after " + str(self._run_number) + " runs: " + str(gain) +
                  ".\nParameters: " + str(best_parameters).translate({ord(c): None for c in '}{'}));
            current_range /= decimal.Decimal(2.0);
            for name in self._parameter_names:
                stop = self._all_parameter_lists[name][-1];
                start = self._all_parameter_lists[name][0];
                new_range = (stop - start) / decimal.Decimal(4.0);
                best_value = best_parameters[name];
                stop = best_value + new_range;
                start = best_value - new_range;
                self.set_parameter_list(name=name,
                                        start=start,
                                        stop=stop,
                                        number_of_points=len(self._all_parameter_lists[name]));
        return self._best_result_of_all_runs;
