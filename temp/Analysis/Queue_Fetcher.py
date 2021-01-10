"""
Created on Jun 2, 2018

@author: me
"""

from Tools.Queue_Handler import Queue_Reader;
from Tools.Database_Handler import Database_Reader;
from Analysis.Fetcher import Fetcher;
import time;
import signal;
from ast import literal_eval;
import decimal;
from threading import Timer;
from Tools.Monitor import Counter, AverageTimer;
from Tools.HelperFunctions import get_current_timestamp, return_human_readable_timestamp;
from Analysis.Actions.TradeManagerFactory import trade_manager_factory;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode, convert_tuple_entries_to_children_names;


class QueueFetcher(Fetcher):
    """
    class docs
    """

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode):
        """
        Constructor
        """
        fetcher_identifier = coin + "_" + self.__class__.__name__.lower();
        super(QueueFetcher, self).__init__(settings_package=settings_package,
                                           coin=coin,
                                           indicator_tree=indicator_tree,
                                           fetcher_identifier=fetcher_identifier);
        self.__indicator_configuration_database_settings = settings_package.get_indicator_database_settings();
        self._mylogger.info("Initiating queue reading module");
        self.__source_queue = Queue_Reader(mq_settings=settings_package.get_message_queue_settings(),
                                           queue_prefix=coin,
                                           function_to_handle_message=self.analyze,
                                           routing_key=coin,
                                           logger_name=fetcher_identifier);
        self._mylogger.info("Initiating monitoring modules");
        # TODO: Check if parameters should go into settings file:
        self.__indicator_update_interval = 30 * 60 * 1000;
        self.__count_data_monitor = Counter(name_prefix=fetcher_identifier,
                                            interval_for_counter_in_ms=30000,
                                            database=settings_package.get_monitor_database_settings(),
                                            logger_name=fetcher_identifier);
        self.__average_time_monitor = AverageTimer(name_prefix=fetcher_identifier,
                                                   no_of_counts=60,
                                                   database=settings_package.get_monitor_database_settings(),
                                                   logger_name=fetcher_identifier);
        self.__trade_manager = trade_manager_factory.create_trade_manager(coin_symbol=self._coin_symbol,
                                                                          logger_name=fetcher_identifier);
        self.__timer_interval_in_sec = 600;  # 10 minutes
        self.__time_without_data_until_shutdown = 900000;  # 15 minutes
        self.__checking_timer = Timer(interval=self.__timer_interval_in_sec,
                                      function=self.__timer_function);
        self.__checking_timer.start();

        # Registering class function "kill_signal_handler" to handle kill signals and CTRL+C
        signal.signal(signal.SIGINT, self.kill_signal_handler);
        signal.signal(signal.SIGTERM, self.kill_signal_handler);

    def __timer_function(self):
        # Updating data in BinanceTradeManager
        self.__trade_manager.fetch_data();
        # Resetting timer
        if self.__checking_timer.is_alive():
            self.__checking_timer.cancel();
        self.__checking_timer = Timer(interval=self.__timer_interval_in_sec,
                                      function=self.__timer_function);
        self.__checking_timer.start();
        # Shutting down if data does not arrive for to long
        if get_current_timestamp() - self._latest_timestamp > self.__time_without_data_until_shutdown:
            self._mylogger.warning("No incoming data since " + return_human_readable_timestamp(self._latest_timestamp) +
                                   "! Current timestamp: " + return_human_readable_timestamp(get_current_timestamp()) +
                                   ". Shutting down. Hoping for restart.");
            self.stop_process();

    def stop_process(self):
        self._mylogger.info("Closing queue connection to stop fetch process");
        self.__source_queue.stop_reading_and_close_connection();
        if self.__checking_timer.is_alive():
            self.__checking_timer.cancel();
        self.__trade_manager.shutdown();
        self.__count_data_monitor.shutdown_monitor();
        self.__average_time_monitor.shutdown_monitor();
        super(QueueFetcher, self).stop_process();
        print("... Analysis stopped.");

    # TODO: Use values?
    def kill_signal_handler(self, signal=None, frame=None):
        self._no_kill_signal = False;
        exit_message = "Caught kill signal! Shutting down!";
        print(exit_message);
        self._mylogger.info(exit_message);
        time.sleep(2);
        self.stop_process();

    def start_process(self):
        self._mylogger.info("Waiting for data collection in queue");
        time.sleep(1);
        """
        Sleep command gives the queue some time to collect data.
        This avoids a data gap between the data set coming from the database and the data coming from the queue
        """
        self._mylogger.info("Initiating start data");
        self._init_data_for_timestamp(timestamp=get_current_timestamp());
        if self._no_kill_signal:
            self._mylogger.info("Starting analysis and trading process");
            print("Starting analysis and trading process ...");
            self.__source_queue.start_reading();  # Start reading from queue
        else:
            self._mylogger.info("... application has been canceled.");
        self.stop_process();

    def analyze(self, data_string):
        self._mylogger.debug("Got data!")
        self.__count_data_monitor.count();
        self.__average_time_monitor.start();
        # Converting incoming string data to tuple of numbers
        data_tuple = literal_eval(data_string);
        final_data = (decimal.Decimal(data_tuple[0]), decimal.Decimal(data_tuple[1]), decimal.Decimal(data_tuple[2]),
                      decimal.Decimal(data_tuple[3]), decimal.Decimal(data_tuple[4]), decimal.Decimal(data_tuple[5]),
                      decimal.Decimal(data_tuple[6]), decimal.Decimal(data_tuple[7]), decimal.Decimal(data_tuple[8]),
                      decimal.Decimal(data_tuple[9]), decimal.Decimal(data_tuple[10]), decimal.Decimal(data_tuple[11]),
                      decimal.Decimal(data_tuple[12]), decimal.Decimal(data_tuple[13]), decimal.Decimal(data_tuple[14]),
                      data_tuple[15], data_tuple[16], data_tuple[17], data_tuple[18], data_tuple[19]);
        self._add_data_to_list(final_data);
        self.__average_time_monitor.stop_and_save();
        if not self._no_kill_signal:
            self.stop_process();

    def _update_indicators(self):
        database = Database_Reader(database_settings=self.__indicator_configuration_database_settings);
        tree_name = database.get_last_entry_from_column(table_name=self._coin_symbol, column="tree_name");
        if tree_name == self._indicator_tree.get_tree_name():
            tree_configuration = database.get_tree_configuration(table_name=self._coin_symbol, tree_name=tree_name);
            for indicator_parameter in tree_configuration:
                identifier = convert_tuple_entries_to_children_names(literal_eval(indicator_parameter[0]));
                print(str(identifier))
                if not self._indicator_tree.update_parameter(identifier=identifier,
                                                             value=indicator_parameter[1]):
                    raise ValueError("Identifier does not fit to indicator tree: " + str(indicator_parameter[0]));
            self._update_indicators_at = get_current_timestamp() + self.__indicator_update_interval;
        else:
            pass;
            # self.stop_process()  # ?? Restart if target tree is currently not used?
