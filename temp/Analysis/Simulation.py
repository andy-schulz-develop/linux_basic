
from Analysis.RandomTrialMultiBacktester import MaxRunsRandomTrialMultiBacktester;
from Analysis.DBBacktester import DBBacktester;
from Tools.HelperFunctions import return_epoch_timestamp, return_human_readable_timestamp;
import time;
# Just for type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;


class Interval(object):
    start_time = 0;
    end_time = 0;


class Simulation(object):

    def __init__(self):
        self.__indicator_test_configuration = {};

    def set_initial_parameter_value(self, identifier: tuple, value, min_value=None, max_value=None):
        self.__indicator_test_configuration[identifier] = {"value": value,
                                                           "min_value": min_value,
                                                           "max_value": max_value};

    @staticmethod
    def generate_time_intervals(start_time: int, end_time: int, interval_size: int, move_interval_by: int) -> list:
        list_of_intervals = [];
        temp_start = start_time;
        temp_end = temp_start + interval_size;
        while temp_end < end_time:
            temp_interval = Interval();
            temp_interval.start_time = return_human_readable_timestamp(temp_start);
            temp_interval.end_time = return_human_readable_timestamp(temp_end);
            list_of_intervals.append(temp_interval);
            temp_start += move_interval_by;
            temp_end += move_interval_by;
        # temp_interval = Interval();
        # temp_interval.start_time = return_human_readable_timestamp(temp_start);
        # temp_interval.end_time = return_human_readable_timestamp(end_time);
        # list_of_intervals.append(temp_interval);
        return list_of_intervals;

    def run_simulation(self,
                       coin: str,
                       start_optimization_at: str,
                       end_run_at: str,
                       interval_size: int,
                       move_interval_by: int,
                       market: Market,
                       indicator_tree: ActionNode,
                       run_name: str = "",
                       amount_of_money=100,
                       results_directory: str = "backtester_results",
                       no_of_runs_per_optimization=5,
                       target_result_csv: str = None):
        results = [];
        i = 0;
        for interval in self.generate_time_intervals(start_time=return_epoch_timestamp(start_optimization_at),
                                                     end_time=return_epoch_timestamp(end_run_at),
                                                     interval_size=interval_size,
                                                     move_interval_by=move_interval_by):
            current_run_name = run_name + str(i) + "_optimization_";
            fetcher = MaxRunsRandomTrialMultiBacktester(initiation_time_string=interval.start_time,
                                                        end_time_string=interval.end_time,
                                                        amount_of_money=amount_of_money,
                                                        settings_package=market,
                                                        coin=coin,
                                                        indicator_tree=indicator_tree,
                                                        run_name=current_run_name,
                                                        results_directory=results_directory,
                                                        max_runs=no_of_runs_per_optimization);
            # Setting initial indicator testing parameters
            if len(results) > 0:
                for test_indicator_values in results[-1].get_indicator_parameters():
                    identifier = test_indicator_values[0];
                    fetcher.set_initial_parameter_value(
                        identifier=identifier,
                        value=test_indicator_values[1],
                        min_value=self.__indicator_test_configuration[identifier]["min_value"],
                        max_value=self.__indicator_test_configuration[identifier]["max_value"]);
            else:
                for identifier, value in self.__indicator_test_configuration.items():
                    fetcher.set_initial_parameter_value(identifier=identifier,
                                                        value=value["value"],
                                                        min_value=value["min_value"],
                                                        max_value=value["max_value"]);
            print("* Green-bar-run:");
            result = fetcher.start_process();
            results.append(result);
            fetcher = None;
            i += 1;
            time.sleep(2);

        indicator_tree.reset_tree();
        fetcher = DBBacktester(
            initiation_time_string=return_human_readable_timestamp(
                return_epoch_timestamp(start_optimization_at)+interval_size),
            end_time_string=end_run_at,
            amount_of_money=amount_of_money,
            settings_package=market,
            coin=coin,
            indicator_tree=indicator_tree,
            run_name=run_name,
            results_directory=results_directory,
            parameter_definitions=results);
        fetcher.start_process();
        fetcher.stop_process();
        fetcher.get_results().write_results_into_csv_file(file_name=target_result_csv);
        print("* Results of final yellow-bar-run:");
        fetcher.get_results().print_results_to_screen();
