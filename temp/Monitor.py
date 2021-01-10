"""
Created on Jun 12, 2018

@author: me
"""

from Tools.HelperFunctions import get_current_timestamp;
from Tools.Database_Handler import CircularDatabaseWriter;
from Tools.DummyDatabase import DummyDatabase;
# Just for type safety
from Settings.ClassImplementations.Database import DatabaseSettings;


class MonitorDatabaseFactory(object):

    __dict_of_databases = {}

    def create_database(self, database_settings: DatabaseSettings = None, logger_name: str = 'application'):
        if isinstance(database_settings, DatabaseSettings):
            database_name = database_settings.get_database_name();
            if database_name in self.__dict_of_databases:
                return self.__dict_of_databases.get(database_name);
            else:
                self.__dict_of_databases[database_name] = CircularDatabaseWriter(database_settings,
                                                                                 logger_name=logger_name);
                return self.__dict_of_databases.get(database_name);
        else:
            if "dummy" in self.__dict_of_databases:
                return self.__dict_of_databases["dummy"];
            else:
                self.__dict_of_databases["dummy"] = DummyDatabase();
                return self.__dict_of_databases["dummy"];

    def __init__(self):
        self.__database = {};
        self.__timestamps = {};

    def add_table(self, table_name):
        self.__database[table_name] = [];
        self.__timestamps[table_name] = 0;

    def add_data(self, table_name, timestamp, value):
        if timestamp > self.__timestamps[table_name]:
            self.__database[table_name].append(value);
            self.__timestamps[table_name] = timestamp;

    def get_data(self, table_name):
        if not self.__database[table_name]:
            return [], [];
        if isinstance(self.__database[table_name][0], tuple):
            '''
            That looks like array([[     2,     10],
                                   [     3,    100],
                                   [     4,   1000],
                                   [     5, 100000]])
            That looks like array([[     2,      3,      4,      5],
                                   [    10,    100,   1000, 100000]])
            '''
            data_in_array = np.array(self.__database[table_name]);
            return data_in_array.T;
        else:
            return self.__database[table_name];


monitor_database_factory = MonitorDatabaseFactory();


class Monitor(object):
    """
    class docs
    """
    def __init__(self, name_prefix: str, database_settings: DatabaseSettings = None, logger_name: str = 'application'):
        """
        Constructor
        """
        self._kpi_name = name_prefix.lower() + "_" + self.__class__.__name__.lower();
        self._start_time = None;
        self.__database = monitor_database_factory.create_database(database_settings=database_settings,
                                                                   logger_name=logger_name);
        self.__database.add_table(self._kpi_name);
        
    def _save_kpi(self, timestamp, value):
        # TODO: Shorten value to avoid database issues
        self.__database.add_data(self._kpi_name, timestamp, (timestamp, float(value)));

    def shutdown_monitor(self):
        self.__database.close_database();


class SaveValue(Monitor):
    """
    class docs
    """

    def __init__(self, name_prefix: str, database: DatabaseSettings = None, logger_name: str = 'application'):
        """
        Constructor
        """
        super(SaveValue, self).__init__(name_prefix=name_prefix, database_settings=database, logger_name=logger_name);

    def save_value(self, value):
        self._save_kpi(get_current_timestamp(), value);


class SaveAverage(Monitor):
    """
    class docs
    """

    def __init__(self,
                 name_prefix: str,
                 no_of_counts: int,
                 database: DatabaseSettings = None,
                 logger_name: str = 'application'):
        """
        Constructor
        """
        super(SaveAverage, self).__init__(name_prefix=name_prefix, database_settings=database, logger_name=logger_name);
        self._counter = 0;
        self._total = 0;
        self._save_after_no_of_counts = no_of_counts;

    def save_value(self, value):
        self._total += value;
        self._counter += 1;
        if self._start_time is None:
            self._start_time = get_current_timestamp();
        if self._counter == self._save_after_no_of_counts:
            measured_value = self._total / self._save_after_no_of_counts;
            # Saving time difference to database
            self._save_kpi(self._start_time, measured_value);
            self._counter = 0;
            self._total = 0;
            self._start_time = None;


class SaveMax(Monitor):
    """
    class docs
    """

    def __init__(self,
                 name_prefix: str,
                 no_of_counts: int,
                 database: DatabaseSettings = None,
                 logger_name: str = 'application'):
        """
        Constructor
        """
        super(SaveMax, self).__init__(name_prefix=name_prefix, database_settings=database, logger_name=logger_name);
        self._counter = 0;
        self._value = 0;
        self._save_after_no_of_counts = no_of_counts;

    def save_value(self, value):
        self._counter += 1;
        if self._start_time is None:
            self._start_time = get_current_timestamp();
            self._value = value;
        if value > self._value:
            self._value = value;
        if self._counter == self._save_after_no_of_counts:
            # Saving maximum value to database
            self._save_kpi(self._start_time, self._value);
            self._counter = 0;
            self._value = 0;
            self._start_time = None;


class SaveMin(Monitor):
    """
    class docs
    """

    def __init__(self,
                 name_prefix: str,
                 no_of_counts: int,
                 database: DatabaseSettings = None,
                 logger_name: str = 'application'):
        """
        Constructor
        """
        super(SaveMin, self).__init__(name_prefix=name_prefix, database_settings=database, logger_name=logger_name);
        self._counter = 0;
        self._value = 0;
        self._save_after_no_of_counts = no_of_counts;

    def save_value(self, value):
        self._counter += 1;
        if self._start_time is None:
            self._start_time = get_current_timestamp();
            self._value = value;
        if value < self._value:
            self._value = value;
        if self._counter == self._save_after_no_of_counts:
            # Saving minimum value to database
            self._save_kpi(self._start_time, self._value);
            self._counter = 0;
            self._value = 0;
            self._start_time = None;


class Counter(Monitor):
    """
    Writes counts per second into database
    Writes roughly every interval_for_counter_in_ms milliseconds into db
    """

    def __init__(self,
                 name_prefix: str,
                 interval_for_counter_in_ms: int,
                 database: DatabaseSettings = None,
                 logger_name: str = 'application'):
        """
        Constructor
        """
        super(Counter, self).__init__(name_prefix=name_prefix, database_settings=database, logger_name=logger_name);
        self._counter = 0;
        self._time_interval_for_counter = interval_for_counter_in_ms;

    def count(self):
        timestamp = get_current_timestamp();
        if self._start_time is None:
            self._counter = 1;
            self._start_time = timestamp;
        elif self._start_time < timestamp - self._time_interval_for_counter:
            # counts_per_interval=self._counter + 1;
            # This normalizes the value to count per ms, but produces float numbers
            counts_per_interval = 1000 * (self._counter + 1) / (timestamp - self._start_time);
            self._save_kpi(self._start_time, counts_per_interval);
            self._counter = 0;
            self._start_time = timestamp;
        else:
            self._counter += 1;


class Timer(Monitor):
    """
    class docs
    """

    def __init__(self, name_prefix: str, database: DatabaseSettings = None, logger_name: str = 'application'):
        """
        Constructor
        """
        super(Timer, self).__init__(name_prefix=name_prefix, database_settings=database, logger_name=logger_name);

    def start(self):
        # Saving current time
        self._start_time = get_current_timestamp();

    def stop_and_save(self):
        timestamp = get_current_timestamp();
        # TODO: Add try: except: block with proper error message for the case stop is executed before start
        if self._start_time is not None:
            # Calculating time difference
            measured_value = timestamp - self._start_time;
            # Saving time difference to database
            self._save_kpi(timestamp, measured_value);
            self._start_time = None;


class AverageTimer(Timer):
    """
    class docs
    """

    def __init__(self,
                 name_prefix: str,
                 no_of_counts: int,
                 database: DatabaseSettings = None,
                 logger_name: str = 'application'):
        """
        Constructor
        """
        super(AverageTimer, self).__init__(name_prefix=name_prefix, database=database, logger_name=logger_name);
        self._counter = 0;
        self._total_time = 0;
        self._save_after_no_of_counts = no_of_counts;

    def stop_and_save(self):
        timestamp = get_current_timestamp();
        self._total_time += timestamp - self._start_time;
        self._counter += 1;
        self._start_time = None;
        if self._counter == self._save_after_no_of_counts:
            measured_value = self._total_time / self._save_after_no_of_counts;
            # Saving time difference to database
            self._save_kpi(timestamp, measured_value);
            self._counter = 0;
            self._total_time = 0;
        # TODO: Add try: except: block with proper error message for the case stop is executed before start
