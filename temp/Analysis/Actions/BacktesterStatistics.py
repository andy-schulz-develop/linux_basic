
import matplotlib.pyplot as plotter;
from decimal import Decimal;
import decimal;
import os;
from Tools.HelperFunctions import get_current_timestamp, return_human_readable_timestamp;
from Settings.Markets import primary_value_index, timestamp_index;
from Analysis.Actions.TradeManager import TradeManager, MarketOperation;
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Analysis.Actions.TradeManagerFactory import trade_manager_factory;
from Tools.Database_Handler import Database_Writer;
# Just for type safety
from Settings.ClassImplementations.Database import DatabaseSettings;


class BacktesterAction(ActionNode):
    """
    class docs
    """

    def __init__(self, default_node, analysis_node=None):
        """
        Constructor
        """
        super(BacktesterAction, self).__init__(default_node=default_node);
        if analysis_node is None:
            self._set_child(name=ChildrenNames.analysis_node, node=default_node);
        else:
            self._set_child(name=ChildrenNames.analysis_node, node=analysis_node);
        self._backtester_statistics = None;
        self.__previous_procession_start_time = 0;
        self.__previous_timestamp = 0;
        self.__previous_price = decimal.Decimal("0.0");
        self.__indicator_parameter_identifier = ();
        self.__indicator_parameter_value = 0;

    def _check_if_instance_is_initialized(self, data_array):
        if self._backtester_statistics is None:
            self._backtester_statistics = trade_manager_factory.get_trade_manager_for_backtesting();
        if len(data_array) < 10:
            return False;
        indicator_tree = self._children.get(ChildrenNames.default_branch);
        self._backtester_statistics.init_values(first_timestamp=data_array[0][timestamp_index],
                                                first_price=data_array[0][primary_value_index],
                                                last_timestamp=data_array[-1][timestamp_index],
                                                last_price=data_array[-1][primary_value_index],
                                                indicator_tree_name=indicator_tree.get_tree_name(),
                                                indicator_tree_information=indicator_tree.print_tree_definition());
        return True;

    def check(self, data_array: list) -> ActionNode:
        if self.__previous_timestamp != 0:
            self._backtester_statistics.collect_values(
                latest_timestamp=self.__previous_timestamp,
                latest_price=self.__previous_price,
                calculation_result=self._children.get(ChildrenNames.analysis_node).get_calculation_result(),
                process_start_time=self.__previous_procession_start_time);
        self.__previous_timestamp = data_array[-1][timestamp_index];
        self.__previous_price = data_array[-1][primary_value_index];
        self.__previous_procession_start_time = get_current_timestamp();
        return self._children.get(ChildrenNames.default_branch);

    def shutdown_indicator(self):
        super(BacktesterAction, self).shutdown_indicator();
        self._backtester_statistics.print_and_plot_results();
        self.reset_tree();

    def update_parameter(self, identifier: tuple, value):
        self._backtester_statistics.collect_indicator_parameter(indicator_parameter_identifier=identifier,
                                                                indicator_parameter_value=value,
                                                                latest_timestamp=self.__previous_timestamp);
        return self._children[ChildrenNames.default_branch].update_parameter(identifier=identifier, value=value);

    def reset_values(self):
        super(BacktesterAction, self).reset_values();
        self._backtester_statistics = None;
        self.__previous_procession_start_time = 0;
        self.__previous_timestamp = 0;
        self.__previous_price = decimal.Decimal("0.0");


class BacktesterResults(object):

    def __init__(self,
                 coin_symbol: str,
                 run_name: str,
                 results_file_name: str,
                 plots_file_name: str,
                 start_time: int,
                 end_time: int,
                 amount_of_money: Decimal):
        self.__coin_symbol = coin_symbol;
        self.__gain = Decimal("0.0");
        self.__gain_w_less_precision_transaction = Decimal("0.0");
        self.__relative_price_change = Decimal("0.0");
        self.__backtesting_started_at = 0;
        self.__start_time = start_time;
        self.__end_time = end_time;
        self.__first_timestamp = 0;
        self.__last_timestamp = 0;
        self.__start_money = Decimal(amount_of_money);
        self.__end_money = Decimal("0.0");
        self.__number_of_buys = 0;
        self.__number_of_sells = 0;
        self.__total_number_of_data_points = 0;
        self.__time_consumed_for_run = 0;
        self.__run_name = run_name;
        self.__results_file_name = results_file_name;
        self.__plots_file_name = plots_file_name;
        self.__indicator_tree_information = "";
        self.__indicator_tree_name = "";
        self.__first_price = Decimal("0.0");
        self.__last_price = Decimal("0.0");
        self.__variance_of_price = Decimal("0.0");
        self.__variance_of_price_derivative = Decimal("0.0");
        self.__indicator_parameters = ();

    def init_values(self,
                    first_timestamp: int,
                    first_price: Decimal,
                    indicator_tree_information: str,
                    indicator_tree_name: str):
        self.__backtesting_started_at = get_current_timestamp();
        self.__first_timestamp = first_timestamp;
        self.__first_price = Decimal(first_price);
        if len(indicator_tree_name) > 0:
            self.__indicator_tree_name = indicator_tree_name;
        else:
            self.__indicator_tree_name = "default_tree";
        self.__indicator_tree_information = indicator_tree_information;

    def __calculate_gain(self, fiat_currency, crypto_currency, latest_price):
        return self.calculate_relative_change(start_money=self.__start_money,
                                              end_money=self.convert_into_fiat(fiat_currency=fiat_currency,
                                                                               crypto_currency=crypto_currency,
                                                                               latest_price=latest_price));

    @staticmethod
    def calculate_relative_change(end_money, start_money):
        return Decimal("100.0") * end_money / start_money - Decimal("100.0");

    @staticmethod
    def convert_into_fiat(fiat_currency: Decimal, crypto_currency, latest_price):
        return fiat_currency + crypto_currency * latest_price;

    def set_results(self,
                    latest_timestamp: int,
                    latest_price: Decimal,
                    fiat_currency: Decimal,
                    crypto_currency: Decimal,
                    total_number_of_data_points: int,
                    number_of_buys: int,
                    number_of_sells: int,
                    variance_of_price=None,
                    variance_of_price_derivative=None,
                    fiat_currency_w_less_precision: Decimal = None,
                    crypto_currency_w_less_precision: Decimal = None):
        self.__gain = self.__calculate_gain(fiat_currency=fiat_currency,
                                            crypto_currency=crypto_currency,
                                            latest_price=latest_price);
        self.__gain_w_less_precision_transaction = \
            self.__calculate_gain(fiat_currency=fiat_currency_w_less_precision,
                                  crypto_currency=crypto_currency_w_less_precision,
                                  latest_price=latest_price);
        self.__relative_price_change = self.calculate_relative_change(end_money=latest_price,
                                                                      start_money=self.__first_price);
        self.__last_timestamp = latest_timestamp;
        self.__last_price = latest_price;
        self.__end_money = self.convert_into_fiat(fiat_currency, crypto_currency, latest_price);
        self.__total_number_of_data_points = total_number_of_data_points;
        self.__number_of_buys = number_of_buys;
        self.__number_of_sells = number_of_sells;
        self.__time_consumed_for_run = (get_current_timestamp() - self.__backtesting_started_at) / 1000.0;
        self.__variance_of_price = variance_of_price;
        self.__variance_of_price_derivative = variance_of_price_derivative;
        if self.__end_time is None:
            self.__end_time = latest_timestamp;

    def get_result_dict(self):
        return {"01-Coin": self.__coin_symbol,
                "07-Start balance": self.__start_money,
                "08-End balance": self.__end_money,
                "04-Price change in %": self.__relative_price_change,
                "02-Gain in %": self.__gain,
                "09-Number of buys": self.__number_of_buys,
                "10-Number of sells": self.__number_of_sells,
                "11-Number of data points": self.__total_number_of_data_points,
                "12-Time needed in sec": self.__time_consumed_for_run,
                "14-Start time": return_human_readable_timestamp(self.__start_time),
                "15-End time": return_human_readable_timestamp(self.__end_time),
                "05-First timestamp": return_human_readable_timestamp(self.__first_timestamp),
                "06-Last timestamp": return_human_readable_timestamp(self.__last_timestamp),
                "16-Variance of price": self.__variance_of_price,
                "17-Variance of price derivative": self.__variance_of_price_derivative,
                "18-Indicator tree name": self.__indicator_tree_name,
                "13-Run name": self.__run_name,
                "Indicator tree information": self.__indicator_tree_information,
                "03-Gain in % with less precision transactions": self.__gain_w_less_precision_transaction};

    def get_results_text(self):
        results = self.get_result_dict();
        max_key_length = len(max(results.keys(), key=len));
        complete_text = "";
        for key in sorted(results.keys()):
            line_to_print = key.ljust(max_key_length) + ": " + str(results[key]);
            complete_text += line_to_print + '\n';
        return complete_text;

    def write_results_into_file(self, result_file_name):
        if result_file_name is not None:
            with open(result_file_name, "a+") as result_file:
                result_file.write(self.get_results_text());

    def print_results_to_screen(self):
        print(self.get_results_text());

    def write_results_into_csv_file(self, file_name):
        exclude_values = ["Indicator tree information"];
        results = self.get_result_dict();
        header_line = "";
        values_line = "";
        with open(file_name, "a+") as result_table_file:
            # Printing column header
            for key in sorted(results.keys()):
                if key not in exclude_values:
                    header_line += "," + str(key);
            for parameter in self.__indicator_parameters:
                header_line += "," + \
                               str(parameter.get_identifier()).replace(",", "-");
            # Printing actual values
            for key in sorted(results.keys()):
                if key not in exclude_values:
                    values_line += "," + str(results[key]);
            for parameter in self.__indicator_parameters:
                values_line += "," + str(parameter.get_value());
            # str(results["Indicator parameters"]).translate({ord(c): None for c in '}{'});
            result_table_file.write(header_line[1:] + '\n' + values_line[1:] + '\n');

    def set_indicator_parameters(self, indicator_parameter_permutation: tuple):
        # Sorting tuple to ensure the order in the result table is always the same
        self.__indicator_parameters = sorted(indicator_parameter_permutation);

    def push_indicator_parameters_to_database(self, database_settings: DatabaseSettings):  # TODO: Remove function
        if len(self.__indicator_parameters) > 0:
            database = Database_Writer(database_settings=database_settings);
            database.add_table(table_name=self.__coin_symbol);
            for parameter in self.__indicator_parameters:
                timestamp = get_current_timestamp();
                database.add_data(table_name=self.__coin_symbol,
                                  timestamp=timestamp,
                                  tupel_with_data=(timestamp,
                                                   self.__indicator_tree_name,
                                                   parameter.get_identifier_for_database(),
                                                   parameter.get_value()));
            database.close_database();

    def get_indicator_parameters(self) -> tuple:
        return self.__indicator_parameters;

    def get_gain(self):
        return self.__gain;

    def get_start_time(self):
        return self.__start_time;

    def get_end_time(self):
        return self.__end_time;

    def __lt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return self.__gain < other.get_gain();

    def __le__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return self.__gain <= other.get_gain();

    def __gt__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return self.__gain > other.get_gain();

    def __ge__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented;
        return self.__gain >= other.get_gain();

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.__gain == other.get_gain();


class BacktesterStatistics(TradeManager):

    def __init__(self,
                 coin_symbol: str,
                 start_time: int,
                 end_time: int,
                 amount_of_money,
                 run_name: str,
                 results_directory: str,
                 print_and_plot: bool = True):
        """
        Constructor
        """
        super(BacktesterStatistics, self).__init__();

        # TODO: Check if parameters should go into settings file:
        self.__transaction_cost = Decimal("0.001");
        self.__tech_quantity_step_size = Decimal("0.01");
        # # # # FOR PLOTTING
        self.__result_plot_rows = 2;
        self.__result_plot_columns = 4;
        self.__plot_number = 1;
        if print_and_plot:
            self.__fig = plotter.figure(figsize=(30, 18));
        else:
            self.__fig = None;

        if run_name is None:
            run_name = "";
        file_name_prefix = results_directory + "/" + run_name;
        results_file_name = file_name_prefix + "_results.txt";
        plots_file_name = file_name_prefix + "_plots.png";
        self.__results_file_name = results_file_name;
        self.__plots_file_name = plots_file_name;
        self.__fiat_currency = Decimal(amount_of_money);
        self.__crypto_currency = Decimal("0.0");
        self.__fiat_currency_w_less_precision_transaction = Decimal(amount_of_money);
        self.__crypto_currency_w_less_precision_transaction = Decimal("0.0");
        self.__latest_timestamp = 0;
        self.__latest_price = Decimal("0.0");
        self.__date = None;
        self.__currently_bought_in = False;
        self.__last_selling_price = Decimal("0.0");
        self.__last_buying_price = Decimal("0.0");
        self._last_operation = MarketOperation.sell;  # TODO: Valid assumption?
        self._sell_is_possible = False;
        self.__print_and_plot = print_and_plot;
        self.__evaluation_finished = False;

        self.__timestamps = [];
        self.__prices = [];
        self.__balance = [];
        self.__time_differences = [];
        self.__calculation_results_of_indicators = [];
        self.__buys_at_time = [];
        self.__sells_at_time = [];
        self.__timestamp_at_transaction = [];
        self.__gain_per_transaction = [];
        self.__average_processing_time = [];
        self.__indicator_parameters = {};
        self.__indicator_parameter_identifiers = [];
        # Creating folder to store results and plots in
        if not os.path.exists(results_directory):
            os.makedirs(results_directory);

        self.__backtester_results = BacktesterResults(coin_symbol=coin_symbol,
                                                      run_name=run_name,
                                                      results_file_name=results_file_name,
                                                      plots_file_name=plots_file_name,
                                                      start_time=start_time,
                                                      end_time=end_time,
                                                      amount_of_money=decimal.Decimal(amount_of_money));

    def init_values(self,
                    first_timestamp: int,
                    first_price: Decimal,
                    last_timestamp: int,
                    last_price: Decimal,
                    indicator_tree_name: str,
                    indicator_tree_information: str):
        self.__latest_timestamp = first_timestamp;
        self.__latest_price = first_price;
        self._last_transaction_time = last_timestamp;
        self._last_transaction_price = last_price;
        date = return_human_readable_timestamp(first_timestamp).split();
        self.__date = date[0];
        self.__backtester_results.init_values(first_price=first_price,
                                              first_timestamp=first_timestamp,
                                              indicator_tree_name=indicator_tree_name,
                                              indicator_tree_information=indicator_tree_information);

    def collect_values(self,
                       latest_timestamp: int,
                       latest_price: Decimal,
                       calculation_result: Decimal,
                       process_start_time: int):
        self.__average_processing_time.append(get_current_timestamp() - process_start_time);
        self.__timestamps.append(latest_timestamp);
        self.__prices.append(latest_price);
        self.__balance.append(
            self.__backtester_results.convert_into_fiat(crypto_currency=self.__crypto_currency,
                                                        latest_price=latest_price,
                                                        fiat_currency=self.__fiat_currency));
        self.__time_differences.append((latest_timestamp - self.__latest_timestamp) / 1000.0);
        self.__calculation_results_of_indicators.append(calculation_result);
        self.__latest_timestamp = latest_timestamp;
        self.__latest_price = latest_price;
        if self.__print_and_plot:
            self.print_results_when_day_switches();

    def collect_indicator_parameter(self,
                                    latest_timestamp: int,
                                    indicator_parameter_identifier: tuple,
                                    indicator_parameter_value):
        if indicator_parameter_identifier in self.__indicator_parameters:
            last_value = self.__indicator_parameters[indicator_parameter_identifier][1][-1];
            self.__indicator_parameters[indicator_parameter_identifier][0].append(self.__latest_timestamp);
            self.__indicator_parameters[indicator_parameter_identifier][0].append(latest_timestamp);
            self.__indicator_parameters[indicator_parameter_identifier][1].append(last_value);
            self.__indicator_parameters[indicator_parameter_identifier][1].append(indicator_parameter_value);
        else:
            self.__indicator_parameters[indicator_parameter_identifier] = [[latest_timestamp],
                                                                           [indicator_parameter_value]];
            self.__indicator_parameter_identifiers.append(indicator_parameter_identifier);

    def sell(self, data_array):
        if self.__currently_bought_in:
            latest_price = data_array[-1][primary_value_index];
            latest_timestamp = data_array[-1][timestamp_index];
            self.__fiat_currency = self.__crypto_currency * latest_price;
            self.__fiat_currency *= Decimal(1) - self.__transaction_cost;
            self.__crypto_currency = Decimal(0.0);
            self.__sells_at_time.append(latest_timestamp);
            self.__currently_bought_in = False;
            self._last_operation = MarketOperation.sell;
            self._last_transaction_time = latest_timestamp;
            self._last_transaction_price = latest_price;
            self._sell_is_possible = False;
            self.__last_selling_price = latest_price;
            self.__timestamp_at_transaction.append(latest_timestamp);
            self.__gain_per_transaction.append(
                self.__backtester_results.calculate_relative_change(start_money=self.__last_buying_price,
                                                                    end_money=latest_price));
            transfer_quantity = self.__crypto_currency_w_less_precision_transaction.quantize(
                self.__tech_quantity_step_size, rounding=decimal.ROUND_DOWN);
            self.__crypto_currency_w_less_precision_transaction -= transfer_quantity;
            self.__fiat_currency_w_less_precision_transaction += \
                transfer_quantity * latest_price * (Decimal(1) - self.__transaction_cost);

    def buy(self, data_array):
        if not self.__currently_bought_in:
            latest_price = data_array[-1][primary_value_index];
            latest_timestamp = data_array[-1][timestamp_index];
            self.__crypto_currency = self.__fiat_currency / latest_price;
            self.__crypto_currency *= Decimal(1) - self.__transaction_cost;
            self.__fiat_currency = Decimal(0.0);
            self.__buys_at_time.append(latest_timestamp);
            self.__currently_bought_in = True;
            self._last_operation = MarketOperation.buy;
            self._last_transaction_time = latest_timestamp;
            self._last_transaction_price = latest_price;
            self._sell_is_possible = True;
            self.__last_buying_price = latest_price;
            # self.__timestamp_at_transaction.append(self.__latest_timestamp);
            # self.__gain_per_transaction.append(self.calculate_relative_change(before=self.__latest_price,
            #                                                                   after=self.__last_selling_price));
            transfer_quantity = self.__fiat_currency_w_less_precision_transaction.quantize(
                self.__tech_quantity_step_size, rounding=decimal.ROUND_DOWN);
            self.__fiat_currency_w_less_precision_transaction -= transfer_quantity;
            self.__crypto_currency_w_less_precision_transaction += \
                transfer_quantity / latest_price * (Decimal(1) - self.__transaction_cost);

    def print_results_when_day_switches(self):
        temp_date = return_human_readable_timestamp(self.__latest_timestamp).split();
        temp_date = temp_date[0];
        if self.__date != temp_date:
            self.__date = temp_date;
            self.__backtester_results.write_results_into_file(result_file_name=self.__results_file_name);

    def add_plot(self, x, y, label, title, legend=True, insert_buy_sell_lines=False):
        axis = self.__fig.add_subplot(self.__result_plot_rows, self.__result_plot_columns, self.__plot_number);
        axis.plot(x, y, label=label);
        if insert_buy_sell_lines:
            self.__insert_vertical_lines(axis=axis, x_values=self.__sells_at_time, label="Sells");
            self.__insert_vertical_lines(axis=axis, x_values=self.__buys_at_time, label="Buys",
                                         color='b',
                                         line_style=(0, (3, 10, 1, 10)));
        if legend:
            axis.legend();
        axis.set_title(title);
        self.__plot_number += 1;
        return axis;

    def add_twin_plot(self, x, y, y2, label, label2, title, insert_buy_sell_lines=False):
        axis = self.__fig.add_subplot(self.__result_plot_rows, self.__result_plot_columns, self.__plot_number);
        axis.plot(x, y, label=label, color='tab:blue');
        axis.set_ylabel(label, color='tab:blue')
        axis2 = axis.twinx();
        axis2.plot(x, y2, label=label2, color='tab:red');
        axis2.set_ylabel(label2, color='tab:red')
        if insert_buy_sell_lines:
            self.__insert_vertical_lines(axis=axis, x_values=self.__sells_at_time, label="Sells");
            self.__insert_vertical_lines(axis=axis, x_values=self.__buys_at_time, label="Buys",
                                         color='b',
                                         line_style=(0, (3, 10, 1, 10)));
        axis.set_title(title);
        self.__plot_number += 1;
        return axis;

    def add_bar_plot(self, y, label, title, legend=True):
        axis = self.__fig.add_subplot(self.__result_plot_rows, self.__result_plot_columns, self.__plot_number);
        x = list(range(len(y)));
        axis.bar(x, y, label=label);
        axis.axhline(y=0, label="Zero line", color="r");
        if legend:
            axis.legend();
        axis.set_title(title);
        self.__plot_number += 1;
        return axis;

    @staticmethod
    def __insert_vertical_lines(axis, x_values, label, color='r', line_style=(0, (1, 10))):
        if x_values:
            axis.axvline(x=x_values[0], color=color, linestyle=line_style, label=label);
            for time_point in x_values:
                axis.axvline(x=time_point, color=color, linestyle=line_style);

    def print_and_plot_results(self) -> BacktesterResults:
        # import numpy;
        # x = numpy.array(self.__timestamps);
        # y = numpy.array(self.__prices);
        # variance_of_price = numpy.var(x);
        # derivative = numpy.diff(y) / numpy.diff(x);
        # variance_of_price_derivative = numpy.var(derivative);

        self.__backtester_results.set_results(
            latest_timestamp=self.__latest_timestamp,
            latest_price=self.__latest_price,
            fiat_currency=self.__fiat_currency,
            crypto_currency=self.__crypto_currency,
            total_number_of_data_points=len(self.__timestamps),
            number_of_buys=len(self.__buys_at_time),
            number_of_sells=len(self.__sells_at_time),
            variance_of_price=Decimal("0.0"),
            variance_of_price_derivative=Decimal("0.0"),
            fiat_currency_w_less_precision=self.__fiat_currency_w_less_precision_transaction,
            crypto_currency_w_less_precision=self.__crypto_currency_w_less_precision_transaction);

        if self.__print_and_plot:
            self.__backtester_results.write_results_into_file(result_file_name=self.__results_file_name);
            # # # # PLOTTING
            # import datetime;
            # import matplotlib.dates
            # from matplotlib.dates import DateFormatter
            # humanTimes = matplotlib.dates.epoch2num(self.__timestamps);
            # self.__fig.autofmt_xdate();
            # axis.xaxis.set_major_formatter(DateFormatter("%d-%m-%y"));

            self.add_plot(x=self.__timestamps, y=self.__prices,
                          label="Price", title="Prices", insert_buy_sell_lines=True);

            self.add_plot(x=self.__timestamps, y=self.__balance,
                          label="Amount of money", title="Amount of money", insert_buy_sell_lines=True);

            self.add_plot(x=self.__timestamps, y=self.__calculation_results_of_indicators,
                          label="Indicator values", title="Indicator values", insert_buy_sell_lines=True);

            self.add_bar_plot(y=self.__gain_per_transaction,
                              label="Gain per transaction in %", title="Gain per transaction in %", legend=False);

            self.add_plot(x=self.__timestamps, y=self.__average_processing_time,
                          label="Time in ms", title="Average processing time of one data point");

            self.add_plot(x=self.__timestamps[1:], y=self.__time_differences[1:],
                          label="Time differences in sec", title="Time differences between each data point");

            # Plotting indicator parameters
            if len(self.__indicator_parameter_identifiers) > 0:
                identifier = self.__indicator_parameter_identifiers[0];
                timestamps = self.__indicator_parameters[identifier][0];
                # First timestamp is 0, replacing it by actual first timestamp
                timestamps[0] = self.__timestamps[0];
                # Prolonging the plot until the actual end
                timestamps.append(self.__timestamps[-1]);
                values = self.__indicator_parameters[identifier][1];
                # Prolonging the plot until the actual end
                values.append(values[-1]);
                if len(self.__indicator_parameter_identifiers) == 1:
                    self.add_plot(x=timestamps, y=values, label=str(identifier), title="Indicator parameter values");
                else:
                    identifier2 = self.__indicator_parameter_identifiers[1];
                    values2 = self.__indicator_parameters[identifier2][1];
                    # Prolonging the plot until the actual end
                    values2.append(values2[-1]);
                    self.add_twin_plot(x=timestamps, y=values, y2=values2,
                                       label=str(identifier), label2=str(identifier2),
                                       title="Indicator parameter values");

            # For this plot self.__timestamps has to be shortened by one
            # self.add_plot(x=self.__timestamps[1:], y=derivative, label="Price derivative", title="Price derivative");

            plotter.figtext(x=0.73, y=0.15, s=self.__backtester_results.get_results_text());
            plotter.draw();  # show
            self.__fig.savefig(self.__plots_file_name);
            plotter.cla();
            plotter.clf();
            plotter.close(self.__fig);
            plotter.close("all");
        self.clear_values();
        self.__evaluation_finished = True;
        return self.__backtester_results;

    def clear_values(self):
        self.__buys_at_time.clear();
        self.__sells_at_time.clear();
        self.__timestamp_at_transaction.clear();
        self.__timestamps.clear();
        self.__prices.clear();
        self.__balance.clear();
        self.__calculation_results_of_indicators.clear();
        self.__gain_per_transaction.clear();
        self.__average_processing_time.clear();
        self.__time_differences.clear();
        self.__indicator_parameters.clear();
        self.__indicator_parameter_identifiers.clear();

    def get_results(self) -> BacktesterResults:
        if not self.__evaluation_finished:
            print("FINAL RESULTS WERE NOT EVALUATED!!" +
                  " MAKE SURE BACKTESTERSTATISTICS.print_and_plot_results WAS CALLED!");
        return self.__backtester_results;
