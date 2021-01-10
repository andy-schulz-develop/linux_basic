
from Analysis.Actions.SimpleIndicator import SimpleIndicator;
from Analysis.Actions.BuySellActions import Buy, Sell;
from Analysis.Actions.Stop_Loss_Indicator import Stop_Loss_Indicator;
from Analysis.Actions.RSI_Indicator import RSI_Indicator;
from Analysis.Actions.MACD_Indicator import MACDIndicator, TimeDependentMACDIndicator, ReverseMACDIndicator;
from Analysis.Actions.WilliamsR_Indicator import WilliamsR_Indicator;
from Analysis.Actions.WorldFormula import WorldFormula;
from Analysis.Actions.TrendIndicator import TrendIndicator;
from Analysis.Actions.BacktesterStatistics import BacktesterAction;

from ast import literal_eval;
from Tools.Database_Handler import Database_Reader;
from Analysis.Actions.ActionNode import ActionNode, convert_tuple_entries_to_children_names, IndicatorParameter;
# Just for type safety
from Analysis.Actions.ActionNode import ActionNode;
from Settings.ClassImplementations.Database import DatabaseSettings;


class ActionTreeFactory(object):

    def __init__(self, coin: str):
        self.__coin = coin;
        self.__buy_action = Buy(coin_symbol=self.__coin, default_node=None);
        self.__sell_action = Sell(coin_symbol=self.__coin, default_node=None);
        self.__tree_creation_methods = {};
        for method in [self.create_tree_world_formula, self.create_tree_macd_indicator,
                       self.create_tree_for_backtesting]:
            self.__tree_creation_methods[method.__name__] = method;

    def change_tree_parameters(self):
        pass

    def create_tree_from_name(self, name: str):  # -> ActionNode
        if name in self.__tree_creation_methods:
            method = self.__tree_creation_methods[name];
            return method();
        else:
            return None;

    def create_tree_for_backtesting(self) -> ActionNode:
        world_formula = WorldFormula(oversold_node=self.__buy_action,
                                     overbought_node=self.__sell_action,
                                     default_node=None,
                                     buy_in_limit=1.029,
                                     sell_limit=0.97);
        world_formula.set_tree_name(name="create_tree_for_backtesting");
        return BacktesterAction(default_node=world_formula, analysis_node=world_formula);

    def create_tree_for_live_processing(self) -> ActionNode:
        world_formula = WorldFormula(oversold_node=self.__buy_action,
                                     overbought_node=self.__sell_action,
                                     default_node=None,
                                     buy_in_limit=1.029,
                                     sell_limit=0.97);
        stop_loss_indicator = Stop_Loss_Indicator(time_interval=100000,
                                                  stop_node=self.__sell_action,
                                                  default_node=world_formula,
                                                  stop_loss_limit=0.992);
        stop_loss_indicator.set_tree_name(name="create_tree_for_live_processing");
        return stop_loss_indicator;

    def build_tree_from_database(self, database_settings: DatabaseSettings) -> ActionNode:
        database = Database_Reader(database_settings=database_settings);
        tree_name = database.get_last_entry_from_column(table_name=self.__coin, column="tree_name");
        indicator_tree = self.create_tree_from_name(name=tree_name);
        tree_configuration = database.get_tree_configuration(table_name=self.__coin, tree_name=tree_name);
        for indicator_parameter in tree_configuration:
            actual_object = IndicatorParameter(tuple_or_identifier=literal_eval(indicator_parameter[0]),
                                               value=indicator_parameter[1]);
            if not indicator_tree.update_parameter(indicator_parameter=actual_object):
                raise ValueError("Identifier does not fit to indicator tree: " + str(actual_object.get_identifier()));
        return indicator_tree;

    def create_tree_with_trend(self) -> ActionNode:
        world_formula2 = WorldFormula(oversold_node=self.__buy_action,
                                      overbought_node=self.__sell_action,
                                      default_node=None,
                                      buy_in_limit=1.01,
                                      sell_limit=0.95)
        world_formula1 = WorldFormula(oversold_node=self.__buy_action,
                                      overbought_node=self.__sell_action,
                                      default_node=None,
                                      buy_in_limit=1.04,
                                      sell_limit=0.99);
        stop_loss1 = Stop_Loss_Indicator(stop_loss_limit="0.9",
                                         stop_node=self.__sell_action,
                                         default_node=world_formula2,
                                         time_interval=100000);
        trend = TrendIndicator(upward_trend_node=stop_loss1,
                               downward_trend_node=world_formula1,
                               default_node=None,
                               time_interval=100*1000)
        return trend;

    def create_tree_with_trend_and_world_formula(self) -> ActionNode:
        world_formula1 = WorldFormula(oversold_node=self.__buy_action,
                                      overbought_node=self.__sell_action,
                                      default_node=None,
                                      buy_in_limit=1.05,
                                      sell_limit=0.9999);
        world_formula2 = WorldFormula(oversold_node=self.__buy_action,
                                      overbought_node=self.__sell_action,
                                      default_node=None,
                                      buy_in_limit=1.0005,
                                      sell_limit=0.99);
        trend = TrendIndicator(upward_trend_node=world_formula2,
                               downward_trend_node=world_formula1,
                               default_node=None,
                               time_interval=33*1000,
                               precision=0.000000001);
        return trend;

    def create_tree_simple_indicator(self) -> ActionNode:
        return SimpleIndicator(oversold_node=self.__buy_action,
                               overbought_node=self.__sell_action,
                               default_node=None,
                               change_limit=1.02);

    def create_tree_rsi_indicator(self) -> ActionNode:
        return RSI_Indicator(time_interval=100000,
                             oversold_node=self.__buy_action,
                             overbought_node=self.__sell_action,
                             default_node=None,
                             buy_limit=30,
                             sell_limit=70);

    def create_tree_macd_indicator(self) -> ActionNode:
        return MACDIndicator(oversold_node=self.__buy_action,
                             overbought_node=self.__sell_action,
                             default_node=None,
                             macd_ema_time_interval=10,
                             slow_ema_time_interval=300,
                             fast_ema_time_interval=2);

    def create_tree_quick_time_macd_indicator(self) -> ActionNode:
        return TimeDependentMACDIndicator(oversold_node=self.__buy_action,
                                          overbought_node=self.__sell_action,
                                          default_node=None,
                                          slow_ema_time_interval=5500 * 1000,
                                          fast_ema_time_interval=23 * 1000,
                                          macd_ema_time_interval=10 * 1000,
                                          precision=0.00000001);

    def create_tree_reverse_macd_indicator(self) -> ActionNode:
        return ReverseMACDIndicator(oversold_node=self.__buy_action,
                                    overbought_node=self.__sell_action,
                                    default_node=None,
                                    macd_ema_time_interval=10,
                                    slow_ema_time_interval=400,
                                    fast_ema_time_interval=2);

    def create_tree_williamsr_indicator(self) -> ActionNode:
        return WilliamsR_Indicator(time_interval=10000,
                                   oversold_node=self.__buy_action,
                                   overbought_node=self.__sell_action,
                                   default_node=None,
                                   overbought_limit=-20,
                                   oversold_limit=-80);

    def create_tree_world_formula(self) -> ActionNode:
        return WorldFormula(oversold_node=self.__buy_action,
                            overbought_node=self.__sell_action,
                            default_node=None,
                            buy_in_limit=1.033,
                            sell_limit=0.97);

    def create_world_formula_for_bnbusdt(self) -> ActionNode:
        return WorldFormula(oversold_node=self.__buy_action,
                            overbought_node=self.__sell_action,
                            default_node=None,
                            buy_in_limit=1.033,
                            sell_limit=0.97);

    def create_world_formula_for_btcusdt(self) -> ActionNode:
        return WorldFormula(oversold_node=self.__buy_action,
                            overbought_node=self.__sell_action,
                            default_node=None,
                            buy_in_limit=1.042,
                            sell_limit=0.989);

    def create_world_formula_for_etcusdt(self) -> ActionNode:
        return WorldFormula(oversold_node=self.__buy_action,
                            overbought_node=self.__sell_action,
                            default_node=None,
                            buy_in_limit=1.078,
                            sell_limit=0.993);

    def create_world_formula_for_linkusdt(self) -> ActionNode:
        return WorldFormula(oversold_node=self.__buy_action,
                            overbought_node=self.__sell_action,
                            default_node=None,
                            buy_in_limit=1.081,
                            sell_limit=0.903);

    def create_world_formula_for_ethusdt(self) -> ActionNode:
        return WorldFormula(oversold_node=self.__buy_action,
                            overbought_node=self.__sell_action,
                            default_node=None,
                            buy_in_limit=1.043,
                            sell_limit=0.971);
