"""
Created on Sep 02, 2019

@author: me
"""
import gc;
from Analysis.DBBacktester import DBBacktester;
import itertools;
import matplotlib.pyplot as plotter;
from Tools.HelperFunctions import get_current_timestamp;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode, IndicatorParameter;
from Analysis.Actions.BacktesterStatistics import BacktesterResults;


class MultiBacktester(object):
    """
    class docs
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
        self._max_parameter = 5;
        self._all_parameter_lists = {};
        self._parameter_names = [];
        self._parameter = {};
        self._best_result_of_all_runs = None;
        self._run_number = 0;

        self._coin_symbol = coin;
        self._indicator_tree = indicator_tree;
        self.__settings_package = settings_package;
        self.__initiation_time_string = initiation_time_string;
        self.__end_time_string = end_time_string;
        self.__amount_of_money = amount_of_money;
        self._results_directory = results_directory;
        self.__verbose_print_and_plot = verbose_print_and_plot;
        self._start_time = 0;
        self._number_of_parameters = 0;
        self._indicator_parameters = {};
        self._list_of_results = [];

        self._run_name = run_name;
        if run_name is None:
            self._run_name = "";
        if self._coin_symbol.lower() not in self._run_name.lower():
            self._run_name = self._coin_symbol + "_" + self._run_name;
        self._default_file_name_prefix = \
            self._results_directory + "/" + self.__class__.__name__.lower() + "_" + self._run_name;
        self._result_table_file_name = self._default_file_name_prefix + "_overall_result_table.csv";

    def set_parameter_values(self, identifier: tuple, values: list):
        named_values = [];
        if identifier not in self._indicator_parameters:
            self._number_of_parameters += 1;
            if self._number_of_parameters > self._max_parameter:
                raise OverflowError("Too many parameters! Just " + str(self._max_parameter) + " parameters supported.");
        else:
            named_values = self._indicator_parameters[identifier];
        for value in values:
            named_values.append(IndicatorParameter(tuple_or_identifier=identifier, value=value));
        self._indicator_parameters[identifier] = named_values;

    def run_over_all_permutations(self):
        keys = list(self._indicator_parameters.keys());
        if self._number_of_parameters == 1:
            for permutation in self._indicator_parameters[keys[0]]:
                self._run_backtester(indicator_parameter_permutation=(permutation, ));
        elif self._number_of_parameters == 2:
            for permutation in itertools.product(self._indicator_parameters[keys[0]],
                                                 self._indicator_parameters[keys[1]]):
                self._run_backtester(indicator_parameter_permutation=permutation);
        elif self._number_of_parameters == 3:
            for permutation in itertools.product(self._indicator_parameters[keys[0]],
                                                 self._indicator_parameters[keys[1]],
                                                 self._indicator_parameters[keys[2]]):
                self._run_backtester(indicator_parameter_permutation=permutation);
        elif self._number_of_parameters == 4:
            for permutation in itertools.product(self._indicator_parameters[keys[0]],
                                                 self._indicator_parameters[keys[1]],
                                                 self._indicator_parameters[keys[2]],
                                                 self._indicator_parameters[keys[3]]):
                self._run_backtester(indicator_parameter_permutation=permutation);
        elif self._number_of_parameters == 5:
            for permutation in itertools.product(self._indicator_parameters[keys[0]],
                                                 self._indicator_parameters[keys[1]],
                                                 self._indicator_parameters[keys[2]],
                                                 self._indicator_parameters[keys[3]],
                                                 self._indicator_parameters[keys[4]]):
                self._run_backtester(indicator_parameter_permutation=permutation);

    def __set_indicator_parameters(self, indicator_parameter_permutation: tuple):
        for parameter in indicator_parameter_permutation:
            if not self._indicator_tree.update_parameter_in_tree_and_reset(identifier=parameter.get_identifier(),
                                                                           value=parameter.get_value()):
                raise ValueError("Identifier does not fit to indicator tree: " + str(parameter.get_identifier()));

    def _run_backtester(self, indicator_parameter_permutation: tuple) -> BacktesterResults:
        # Setting up the Backtester
        single_backtester = DBBacktester(initiation_time_string=self.__initiation_time_string,
                                         end_time_string=self.__end_time_string,
                                         amount_of_money=self.__amount_of_money,
                                         settings_package=self.__settings_package,
                                         coin=self._coin_symbol,
                                         indicator_tree=self._indicator_tree,
                                         run_name=self._run_name + str(self._run_number),
                                         results_directory=self._results_directory,
                                         print_and_plot=self.__verbose_print_and_plot);
        # Setting indicator parameters - IMPORTANT: Has to happen after setting up the backtester!
        self.__set_indicator_parameters(indicator_parameter_permutation=indicator_parameter_permutation);
        # Clean up memory before new data is allocated
        gc.collect();
        # Actually starting the backtester
        single_backtester.start_process();
        single_backtester.stop_process();
        results_of_single_run = single_backtester.get_results();

        # Adding indicator parameters to results
        results_of_single_run.set_indicator_parameters(indicator_parameter_permutation=indicator_parameter_permutation);

        # Checking if current result is better than results before
        if self._best_result_of_all_runs is None:
            self._best_result_of_all_runs = results_of_single_run;
        if results_of_single_run > self._best_result_of_all_runs:
            self._best_result_of_all_runs = results_of_single_run;
        self._run_number += 1;

        # Calculating average processing time
        self._average_processing_time_per_run = \
            (get_current_timestamp() - self._start_time + 4000) / self._run_number / 1000;

        results_of_single_run.write_results_into_csv_file(file_name=self._result_table_file_name);

        # Individual post processing
        self._post_processing(backtester_result=results_of_single_run);
        return results_of_single_run;

    def start_process(self):
        if self._number_of_parameters < 1:
            raise ValueError("Not enough parameters specified for testing! Please set parameter values!");

    def _post_processing(self, backtester_result: BacktesterResults):
        pass;

    def get_best_result(self) -> BacktesterResults:
        return self._best_result_of_all_runs;

    def _plot_summary(self):
        if self._number_of_parameters == 1:
            # Setting file names for result files
            result_plot_file_name = self._default_file_name_prefix + "_overall_result_plot.png";

            # Preparing data for final plotting and filling result table in csv
            gain_list = [];
            first_parameter_list = [];
            for result in self._list_of_results:
                gain_list.append(result.get_gain());
                first_parameter_list.append(result.get_first_parameter());

            # Actual plotting
            fig, ax = plotter.subplots();
            ax.plot(first_parameter_list, gain_list);
            ax.set(xlabel='Parameter value', ylabel='Gain in percent');  # title='abd'
            ax.grid()
            plotter.draw();  # show
            fig.savefig(result_plot_file_name);
            plotter.cla();
            plotter.clf();
            plotter.close("all");
        elif self._number_of_parameters == 2:
            # Setting file names for result files
            result_plot_file_name = self._default_file_name_prefix + "_overall_result_plot.png";

            # Preparing data for final plotting and filling result table in csv
            gain_list = [];
            first_parameter_list = [];
            second_parameter_list = [];
            for result in sorted(self._list_of_results):
                gain_list.append(result.get_gain());
                first_parameter_list.append(result.get_first_parameter());
                second_parameter_list.append(result.get_second_parameter());
            max_gain = self._best_result_of_all_runs.get_gain();
            min_gain = min(gain_list);
            plotting_limit = max([max_gain, abs(min_gain)]);

            # Actual plotting
            fig = plotter.figure(figsize=(24, 18));
            fig.add_subplot(1, 1, 1);
            plotter.scatter(first_parameter_list,
                            second_parameter_list,
                            c=gain_list,
                            s=1500, cmap='gist_rainbow', vmin=-1 * plotting_limit, vmax=plotting_limit);
            c_bar = plotter.colorbar();
            c_bar.minorticks_on();
            # plotter.show();
            plotter.draw();  # show
            fig.savefig(result_plot_file_name);
            plotter.cla();
            plotter.clf();
            plotter.close("all");
            # plotter.close(fig=fig);
        self._list_of_results.clear();
