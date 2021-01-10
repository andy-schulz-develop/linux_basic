"""
Created on Sep 02, 2019

@author: me
"""
from Analysis.MultiBacktester import MultiBacktester;
from Tools.HelperFunctions import get_current_timestamp, return_human_readable_timestamp, return_epoch_timestamp;
import signal;
import decimal;
import random;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;
from Analysis.Actions.BacktesterStatistics import BacktesterResults;


class RandomTrialMultiBacktester(MultiBacktester):
    """
    RandomTrialMultiBacktester
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
                 verbose_print_and_plot: bool = False):
        """
        Constructor
        """
        super(RandomTrialMultiBacktester, self).__init__(settings_package=settings_package,
                                                         coin=coin,
                                                         indicator_tree=indicator_tree,
                                                         initiation_time_string=initiation_time_string,
                                                         end_time_string=end_time_string,
                                                         run_name=run_name,
                                                         amount_of_money=amount_of_money,
                                                         results_directory=results_directory,
                                                         verbose_print_and_plot=verbose_print_and_plot);
        self.__no_kill_signal = True
        self.__lower_limits = {};
        self.__upper_limits = {};
        # Registering class function "kill_signal_handler" to handle kill signals and CTRL+C
        signal.signal(signal.SIGINT, self.kill_signal_handler);
        signal.signal(signal.SIGTERM, self.kill_signal_handler);

    @staticmethod
    def __return_varying_values(initial_value, min_value=None, max_value=None):
        if isinstance(initial_value, int):
            if max_value is None:
                upper_limit = int(round(1.5 * initial_value));
            else:
                upper_limit = int(max_value);
            if min_value is None:
                lower_limit = int(round(0.5 * initial_value));
            else:
                lower_limit = int(min_value);
            return [initial_value,
                    random.randrange(lower_limit, initial_value),
                    random.randrange(initial_value, upper_limit)];
        elif isinstance(initial_value, float) or isinstance(initial_value, decimal.Decimal):
            if max_value is None:
                upper_limit = 1.5 * float(initial_value);
            else:
                upper_limit = float(max_value);
            if min_value is None:
                lower_limit = 0.5 * float(initial_value);
            else:
                lower_limit = float(min_value);
            return [decimal.Decimal(str(initial_value)),
                    decimal.Decimal(str(random.uniform(lower_limit, float(initial_value)))),
                    decimal.Decimal(str(random.uniform(float(initial_value), upper_limit)))];

    def set_initial_parameter_value(self, identifier: tuple, value, min_value=None, max_value=None):
        self.__lower_limits[identifier] = min_value;
        self.__upper_limits[identifier] = max_value;
        self.set_parameter_values(identifier=identifier, values=self.__return_varying_values(initial_value=value,
                                                                                             min_value=min_value,
                                                                                             max_value=max_value));

    def _post_processing(self, backtester_result: BacktesterResults):
        if self._run_number < 1000:
            self._list_of_results.append(backtester_result);
        print("Run No. " + str(self._run_number) + " finished. Average processing time: " +
              "{:8.2f}sec.".format(self._average_processing_time_per_run));
        return backtester_result;

    def _exit_condition_fulfilled(self):
        return not self.__no_kill_signal;

    def start_process(self):
        super(RandomTrialMultiBacktester, self).start_process();
        print("Starting first run");
        self._start_time = get_current_timestamp();
        while not self._exit_condition_fulfilled() and self.__no_kill_signal:
            self.run_over_all_permutations();
            parameters = self._best_result_of_all_runs.get_indicator_parameters();
            for parameter_set in parameters:
                identifier = parameter_set[0];
                value = parameter_set[1];
                self.set_initial_parameter_value(identifier=identifier,
                                                 value=value,
                                                 min_value=self.__lower_limits[identifier],
                                                 max_value=self.__upper_limits[identifier]);
        self._plot_summary();
        print("Best run: ");
        self._best_result_of_all_runs.print_results_to_screen();
        return self._best_result_of_all_runs;

    # TODO: Use values?
    def kill_signal_handler(self, signal=None, frame=None):
        self.__no_kill_signal = False;
        all_values = list(self._indicator_parameters.values());
        runs_in_a_bunch = len(all_values[0]) ** self._number_of_parameters;
        remaining_number_of_runs = runs_in_a_bunch - (self._run_number % runs_in_a_bunch);
        exit_message = "Caught kill signal! Finishing up last " + str(remaining_number_of_runs) + \
                       " runs and shutting down afterwards";
        print(exit_message);


class ContinuousRandomTrialMultiBacktester(RandomTrialMultiBacktester):
    """
    ContinuousRandomTrialMultiBacktester
    """

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 initiation_time_string: str,
                 max_run_time: int,
                 run_name: str = "",
                 amount_of_money=100,
                 results_directory: str = "backtester_results",
                 verbose_print_and_plot: bool = False):
        """
        Constructor
        """
        super(ContinuousRandomTrialMultiBacktester, self).__init__(
            settings_package=settings_package,
            coin=coin,
            indicator_tree=indicator_tree,
            initiation_time_string=initiation_time_string,
            end_time_string=return_human_readable_timestamp(get_current_timestamp()),
            run_name=run_name,
            amount_of_money=amount_of_money,
            results_directory=results_directory,
            verbose_print_and_plot=verbose_print_and_plot);
        self.__jump_time_interval = max_run_time;
        self.__change_end_time_at = return_epoch_timestamp(self.__end_time_string) + max_run_time;

    def _exit_condition_fulfilled(self):
        if get_current_timestamp() > self.__change_end_time_at:
            self.__end_time_string = return_human_readable_timestamp(self.__change_end_time_at);
            self.__change_end_time_at += self.__jump_time_interval;
            return True;
        else:
            return False;


class MaxRunsRandomTrialMultiBacktester(RandomTrialMultiBacktester):
    """
    MaxRunsRandomTrialMultiBacktester
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
                 verbose_print_and_plot: bool = False,
                 max_runs: int = 300):
        """
        Constructor
        """
        super(MaxRunsRandomTrialMultiBacktester, self).__init__(settings_package=settings_package,
                                                                coin=coin,
                                                                indicator_tree=indicator_tree,
                                                                initiation_time_string=initiation_time_string,
                                                                end_time_string=end_time_string,
                                                                run_name=run_name,
                                                                amount_of_money=amount_of_money,
                                                                results_directory=results_directory,
                                                                verbose_print_and_plot=verbose_print_and_plot);
        self.__maximum_runs = max_runs;

    def _exit_condition_fulfilled(self):
        if self._run_number > self.__maximum_runs:
            return True;
        else:
            return False;


class MaxTimeRandomTrialMultiBacktester(RandomTrialMultiBacktester):
    """
    MaxTimeRandomTrialMultiBacktester
    """

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 initiation_time_string: str,
                 end_time_string: str,
                 max_run_time: int,
                 run_name: str = "",
                 amount_of_money=100,
                 results_directory: str = "backtester_results",
                 verbose_print_and_plot: bool = False):
        """
        Constructor
        """
        super(MaxTimeRandomTrialMultiBacktester, self).__init__(
            settings_package=settings_package,
            coin=coin,
            indicator_tree=indicator_tree,
            initiation_time_string=initiation_time_string,
            end_time_string=end_time_string,
            run_name=run_name,
            amount_of_money=amount_of_money,
            results_directory=results_directory,
            verbose_print_and_plot=verbose_print_and_plot);
        self.__stop_at = get_current_timestamp() + max_run_time;

    def _exit_condition_fulfilled(self):
        if get_current_timestamp() > self.__stop_at:
            return True;
        else:
            return False;
