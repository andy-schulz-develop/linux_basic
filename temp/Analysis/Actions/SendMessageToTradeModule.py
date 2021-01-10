
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Tools.Queue_Handler import Queue_Writer;
from Settings.Markets import timestamp_index, primary_value_index;
# Just for type safety
from Settings.ClassImplementations.MQ import MessageQueueSettings;


class SendMessageToTradeModule(ActionNode):
    """
    Puts a message into a queue
    """

    def __init__(self,
                 message_queue_settings: MessageQueueSettings,
                 coin_symbol: str,
                 default_node: ActionNode = None):
        """
        Constructor
        """
        super(SendMessageToTradeModule, self).__init__(default_node=default_node);
        self._set_parameter(name="coin_symbol", parameter=coin_symbol);
        self.__mq_settings = message_queue_settings;

    def _send(self, mode: str, data_array):
        price = float(data_array[-1][primary_value_index]);
        timestamp = data_array[-1][timestamp_index];
        message = {"mode": mode, "price": price, "trigger_timestamp": timestamp};

        queue = Queue_Writer(self.__mq_settings);
        queue.write_message(self._parameters["coin_symbol"], message);
        queue.close_connection();


class SendBuyMessage(SendMessageToTradeModule):

    def check(self, data_array) -> ActionNode:
        self._send(mode="buy", data_array=data_array)
        return self._children.get(ChildrenNames.default_branch);


class SendSellMessage(SendMessageToTradeModule):

    def check(self, data_array) -> ActionNode:
        self._send(mode="sell", data_array=data_array)
        return self._children.get(ChildrenNames.default_branch);
