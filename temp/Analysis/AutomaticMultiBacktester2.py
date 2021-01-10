"""
Created on Sep 02, 2019

@author: me
"""
from Analysis.MultiBacktester import MultiBacktester;
import decimal;
from operator import itemgetter;


class AutomaticMultiBacktester2(MultiBacktester):
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
        super(AutomaticMultiBacktester2, self).__init__(name_of_target_indicator_node=name_of_target_indicator_node,
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
        self.__results_of_each_run = [];

    def _backtester_wrapper(self):
        results_of_single_run = self._run_backtester();
        self.__results_of_each_run.append(results_of_single_run);
        self.write_results_into_csv_file(results_of_single_run, self.__result_table_file_name);
        print("Run No. " + str(self._run_number) + " finished.");
        return results_of_single_run;

    def start_process(self):
        super(AutomaticMultiBacktester2, self).start_process();
        previous_gain = decimal.Decimal(-99999.009);
        gain = previous_gain + self.__min_search_interval + decimal.Decimal(1.0);
        self.__min_search_interval *= self._all_parameter_lists[self._parameter_names[0]][0];
        current_range = self._all_parameter_lists[self._parameter_names[0]][-1] -\
                        self._all_parameter_lists[self._parameter_names[0]][0];
        # TODO: Check if additional interval condition required (see below)
        while current_range > self.__min_search_interval:
            # while abs(gain - previous_gain) > self.__gain_precision:
            self.__results_of_each_run = [];
            self._iterate_over_parameter_lists();
            previous_gain = gain;
            gain = self._best_result_of_all_runs["Gain in %"];
            current_range /= decimal.Decimal(2.0);
            sorted_results_of_each_run = sorted(self.__results_of_each_run, key=itemgetter("Gain in %"), reverse=True);
            for name in self._parameter_names:
                stop = sorted_results_of_each_run[0]["Indicator parameters"][name] * decimal.Decimal(1.01);
                start = sorted_results_of_each_run[0]["Indicator parameters"][name] / decimal.Decimal(1.01);
                for i in range(1, 5, 1):
                    parameter_value = sorted_results_of_each_run[i]["Indicator parameters"][name];
                    if parameter_value > stop:
                        stop = parameter_value;
                    if parameter_value < start:
                        start = parameter_value;
                self.set_parameter_list(name=name,
                                        start=start,
                                        stop=stop,
                                        number_of_points=len(self._all_parameter_lists[name]));
                print("Maximum gain after " + str(self._run_number) + " runs: " + str(gain) +
                      ".\nParameters: " + str(self._all_parameter_lists[name][0]) +
                      ".\nParameters: " + str(self._all_parameter_lists[name][-1]));
                print(str(self._all_parameter_lists));
        return self._best_result_of_all_runs;
