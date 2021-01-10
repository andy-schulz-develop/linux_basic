
import time
import pandas;
import gc;
from Tools.HelperFunctions import DEFAULT_DATE_FORMAT, convert_string_into_datetime;
from Settings.Markets import binance;
from Analysis.Actions.ActionTreeFactory import ActionTreeFactory;
from Analysis.Actions.ActionNode import convert_tuple_entries_to_children_names;
from Analysis.Simulation import Simulation;
from ast import literal_eval;
from Tools.EmailSender import EmailSender;
# Just for type safety
from Settings.ClassImplementations.Markets import Market;


def run_csv_data(data_source_file: str, market: Market = binance, send_mail: bool = True):
    results_directory_date_format = "%Y_%m_%d";
    required_columns = {"coin", "indicator_tree", "results_directory", "target_result_csv", "interval_size",
                        "move_interval_by", "no_of_runs_per_optimization", "start_optimization_at", "end_run_at"};
    data_frame = pandas.read_csv(data_source_file);

    existing_columns = set(data_frame.columns);
    if len(required_columns - existing_columns) > 0:
        raise ValueError("Input table does not contain all required columns. These columns are missing: " +
                         str(required_columns - existing_columns));
    for index, row in data_frame.iterrows():
        for row_name in ["coin", "indicator_tree", "results_directory", "target_result_csv"]:
            if not isinstance(row[row_name], str):
                raise ValueError("Incorrect data format in line " + str(index) + " column '" +
                                 row_name + "', should be a string");
        for row_name in ["interval_size", "move_interval_by", "no_of_runs_per_optimization"]:
            if not isinstance(row[row_name], int):
                raise ValueError("Incorrect data format in column '" + row_name + "', should be integer");
        for row_name in ["start_optimization_at", "end_run_at"]:
            try:
                convert_string_into_datetime(row[row_name]);
            except ValueError as e:
                raise ValueError("Incorrect date format in line " + str(index) + " column '" +
                                 row_name + "', see: " + str(e));

    for index, row in data_frame.iterrows():
        coin = row["coin"];
        input_date_for_start_optimization_at = convert_string_into_datetime(row["start_optimization_at"]);
        start_optimization_at = input_date_for_start_optimization_at.strftime(DEFAULT_DATE_FORMAT);
        input_date_for_end_run_at = convert_string_into_datetime(row["end_run_at"]);
        end_run_at = input_date_for_end_run_at.strftime(DEFAULT_DATE_FORMAT);
        interval_size = row["interval_size"] * 24 * 60 * 60 * 1000;
        move_interval_by = row["move_interval_by"] * 24 * 60 * 60 * 1000;
        no_of_runs_per_optimization = row["no_of_runs_per_optimization"];
        results_directory = row["results_directory"];
        while results_directory.endswith("/") or results_directory.endswith("\\"):
            results_directory = results_directory[:-1];
        results_directory += "_" + input_date_for_start_optimization_at.strftime(results_directory_date_format) + \
                             "__" + input_date_for_end_run_at.strftime(results_directory_date_format) + \
                             "_GREEN_" + str(row["interval_size"]) + \
                             "D_YELLOW_" + str(row["move_interval_by"]) + \
                             "D_" + str(no_of_runs_per_optimization) + "_" + coin;

        tree_factory = ActionTreeFactory(coin=coin);
        indicator_tree = tree_factory.create_tree_from_name(name=row["indicator_tree"]);

        non_default_columns = existing_columns - required_columns;
        simulator = Simulation();

        indicator_parameters = {};
        for parameter_string_identifier in non_default_columns:
            # Convert column header (string) to Python list
            helper_var_for_identifier = list(literal_eval(parameter_string_identifier));
            # Filter out keywords like 'min', 'max', 'value'
            helper_var_for_identifier = tuple(x for x in helper_var_for_identifier if x.lower() not in "maxminvalue");
            # Convert strings in tuple to real Children_names
            identifier = convert_tuple_entries_to_children_names(helper_var_for_identifier);
            if identifier in indicator_parameters:
                indicator_parameters[identifier].append(row[parameter_string_identifier]);
            else:
                indicator_parameters[identifier] = [row[parameter_string_identifier]];
        for indicator_parameter_identifier, indicator_parameter_values in indicator_parameters.items():
            if len(indicator_parameter_values) == 3:
                indicator_parameter_values.sort();
                simulator.set_initial_parameter_value(identifier=indicator_parameter_identifier,
                                                      value=indicator_parameter_values[1],
                                                      max_value=indicator_parameter_values[2],
                                                      min_value=indicator_parameter_values[0]);
            elif len(indicator_parameter_values) == 1:
                simulator.set_initial_parameter_value(identifier=indicator_parameter_identifier,
                                                      value=indicator_parameter_values[0]);

        simulator.run_simulation(start_optimization_at=start_optimization_at,
                                 end_run_at=end_run_at,
                                 interval_size=interval_size,
                                 move_interval_by=move_interval_by,
                                 amount_of_money=100,
                                 market=market,
                                 coin=coin,
                                 indicator_tree=indicator_tree,
                                 run_name="run",
                                 results_directory=results_directory,
                                 no_of_runs_per_optimization=no_of_runs_per_optimization,
                                 target_result_csv=row["target_result_csv"]);
        time.sleep(2);
        gc.collect();
    if send_mail:
        email_sender = EmailSender();
        email_sender.send_mail_via_host(message="Run is finished!");
