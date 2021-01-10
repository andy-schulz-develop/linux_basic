"""
Created on Jun 2, 2018

@author: me
"""
from Tools.LoggerCreator import LoggerCreator;
from Tools.Database_Handler import Database_Reader;
from Tools.HelperFunctions import return_human_readable_timestamp, get_current_timestamp, VERY_HIGH_INTEGER;
from Settings.Markets import timestamp_index;
from Analysis.Actions.ActionTreeFactory import ActionTreeFactory;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;


class Fetcher(object):
    """
    class docs
    """
    _no_kill_signal = True;

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 fetcher_identifier: str = ""):
        """
        Constructor
        """
        if len(fetcher_identifier) < 1:
            self._fetcher_identifier = coin + "_" + self.__class__.__name__.lower();
        else:
            self._fetcher_identifier = fetcher_identifier;
        self._mylogger = LoggerCreator.createLogger(name=self._fetcher_identifier,
                                                    logfile_filename=self._fetcher_identifier + ".log");
        self._coin_symbol = coin;
        # TODO: Consider using numpy array or other data type
        self._data = [];
        self._latest_timestamp = 0;

        self._mylogger.info("Initiating fetcher " + self._fetcher_identifier);
        if isinstance(indicator_tree, str):
            tree_factory = ActionTreeFactory(coin=coin);
            self._indicator_tree = tree_factory.create_tree_from_name(name=indicator_tree);
        elif isinstance(indicator_tree, ActionNode):
            self._indicator_tree = indicator_tree;
        self._max_time_interval_in_ms = self._indicator_tree.get_max_tree_time_interval() + 1000;
        self.__database_settings = settings_package.get_analyzer_database_settings();
        # TODO: Put into settings?
        self._max_number_of_data_points_loaded_at_once = 200000;
        self._max_initialization_time_range = 365 * 24 * 60 * 60 * 1000;  # 1 year
        self._update_indicators_at = VERY_HIGH_INTEGER;  # Must be VERY high, will be updated to appropriate value later
        self._trade_manager = None;

    def _init_data_for_timestamp(self, timestamp):
        preparation_time = 1000000;
        initialization_complete = False;
        number_of_data_points = 0;
        data_list = None;
        while not initialization_complete \
                and preparation_time < self._max_initialization_time_range \
                and 2 * number_of_data_points < self._max_number_of_data_points_loaded_at_once:
            data_list, reached_end_of_interval, number_of_data_points =\
                self._fetch_from_database(begin=timestamp - preparation_time, end=timestamp);
            initialization_complete = self._indicator_tree.init_indicator(data_list);
            preparation_time *= 2;
        if initialization_complete:
            self._data = data_list;
            self._latest_timestamp = data_list[-1][timestamp_index];
        else:
            self._no_kill_signal = False;
            raise OverflowError("Gathering data for initialization takes too much effort. Either initialization " +
                                "of indicator tree requires too much data OR database does not contain enough data. " +
                                "Last used search time in ms: " + str(preparation_time));

    def _fetch_from_database(self, begin: int, end: int) -> tuple:
        self._mylogger.info("Loading data from database");
        # TODO: contextManager nutzen!!!!
        database = Database_Reader(self.__database_settings, logger_name=self._fetcher_identifier);
        total_number_of_points = database.count_lines_in_time_range(table_name=self._coin_symbol,
                                                                    start_time=begin,
                                                                    end_time=end);
        if total_number_of_points == 0:
            error_message = "Could not load data from database. Either there is no data in time interval " + \
                            return_human_readable_timestamp(begin) + \
                            " and " + return_human_readable_timestamp(end) + \
                            " or there are problems with the connection to the database.";
            self._mylogger.warning(error_message);
            return [], True, 0;
            # raise ValueError(error_message);  # OR: return [], True, 0;
        number_of_points_in_interval = total_number_of_points;
        new_end = end;
        if end is None and number_of_points_in_interval > self._max_number_of_data_points_loaded_at_once:
            new_end = get_current_timestamp();
        # Move end of interval nearer to beginning until number of point is below defined maximum
        while number_of_points_in_interval > self._max_number_of_data_points_loaded_at_once:
            new_end = int((new_end + begin) / 2);
            number_of_points_in_interval = database.count_lines_in_time_range(table_name=self._coin_symbol,
                                                                              start_time=begin,
                                                                              end_time=new_end);
        data = database.get_complete_lines_in_time_range(table_name=self._coin_symbol,
                                                         start_time=begin,
                                                         end_time=new_end);
        database.close_database();
        if not data:
            self._mylogger.warning("Could not load data from database. Either there is no data in time interval " +
                                   return_human_readable_timestamp(begin) + " and " +
                                   return_human_readable_timestamp(end) +
                                   " or there are problems with the connection to the database.");
            return data, True, 0;
        self._mylogger.info("Loaded data from database starting at " + return_human_readable_timestamp(begin) +
                            " Ending " + return_human_readable_timestamp(new_end) +
                            " Number of points: " + str(len(data)));
        # To check whether the interval was split or loaded at once
        if new_end == end:
            return data, True, total_number_of_points;
        else:
            return data, False, total_number_of_points;

    def _add_data_to_list(self, data_point):
        if data_point is not None:
            if data_point[timestamp_index] > self._latest_timestamp:
                self._data.append(data_point);
                self._latest_timestamp = data_point[timestamp_index];
                self._data.pop(0);
                if self._latest_timestamp >= self._update_indicators_at:
                    self._update_indicators();
                tree_node = self._indicator_tree;
                while tree_node is not None:
                    try:
                        self._mylogger.debug("Starting tree node: " + tree_node.get_indicator_name());
                        tree_node = tree_node.check(self._data);
                    except Exception as e:
                        self._mylogger.exception(e);
                        exit_message = "Critical error occurred!\n" + str(e) + "\nShutting down, hoping for restart.";
                        print(exit_message);
                        self._mylogger.warning(exit_message);
                        self._no_kill_signal = False;
                        self.stop_process();
                        raise e;

    def _update_indicators(self):
        pass;

    def analyze(self, data):
        pass;

    def start_process(self):
        pass;

    def stop_process(self):
        self._indicator_tree.shutdown_indicator();
        LoggerCreator.shutdown();
