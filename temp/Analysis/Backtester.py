"""
Created on Apr 28, 2018

@author: me
"""
from Analysis.Fetcher import Fetcher;
from Analysis.Actions.BacktesterStatistics import BacktesterStatistics, BacktesterResults, BacktesterAction;
from Analysis.Actions.TradeManagerFactory import trade_manager_factory;
from Tools.HelperFunctions import return_epoch_timestamp, VERY_HIGH_INTEGER;
# Just for IDE type safety
from Settings.ClassImplementations.Markets import Market;
from Analysis.Actions.ActionNode import ActionNode;


class Backtester(Fetcher):
    """
    class docs
    """
    __progress = 0.0;

    def __init__(self,
                 settings_package: Market,
                 coin: str,
                 indicator_tree: ActionNode,
                 initiation_time_string: str,
                 end_time_string=None,
                 run_name: str = "",
                 amount_of_money=100,
                 results_directory: str = "backtester_results",
                 parameter_definitions: list = None,
                 print_and_plot: bool = True):
        """
        Constructor
        """
        if not isinstance(indicator_tree, BacktesterAction):
            indicator_tree = BacktesterAction(default_node=indicator_tree);
        super(Backtester, self).__init__(settings_package=settings_package,
                                         coin=coin,
                                         indicator_tree=indicator_tree);
        # date_string has to be this format: "2018-06-23 22:09:00"
        start_time = return_epoch_timestamp(date_string=initiation_time_string);
        self._start_time = start_time;
        if end_time_string is not None:
            self._end_time = return_epoch_timestamp(date_string=end_time_string);
            if self._end_time < self._start_time:
                raise ValueError("Start time '" + initiation_time_string + "' is later than end time '" +
                                 end_time_string + "'!");
        else:
            self._end_time = None;
        if self._start_time < 946688400000:  # 1st January Year 2000
            raise ValueError("Start time '" + initiation_time_string + "' is too far in the past!");
        self._trade_manager = BacktesterStatistics(
            coin_symbol=coin,
            start_time=start_time,
            end_time=self._end_time,
            amount_of_money=amount_of_money,
            run_name=run_name,
            results_directory=results_directory,
            print_and_plot=print_and_plot);
        trade_manager_factory.set_trade_manager_for_backtesting(trade_manager=self._trade_manager);
        self.__parameter_definitions = parameter_definitions;
        if parameter_definitions is not None and len(parameter_definitions) > 1:
            self._update_indicators_at = parameter_definitions[1].get_end_time();

    def start_process(self):
        pass;

    def get_results(self) -> BacktesterResults:
        return self._trade_manager.get_results();

    def _update_indicators(self):
        parameter_definition = self.__parameter_definitions.pop(0);
        for indicator_parameter in parameter_definition.get_indicator_parameters():
            if not self._indicator_tree.update_parameter(identifier=indicator_parameter[0],
                                                         value=indicator_parameter[1]):
                raise ValueError("Identifier does not fit to indicator tree: " + str(indicator_parameter[0]));
        if len(self.__parameter_definitions) > 1:
            self._update_indicators_at = self.__parameter_definitions[1].get_end_time();
        else:
            self._update_indicators_at = VERY_HIGH_INTEGER;
