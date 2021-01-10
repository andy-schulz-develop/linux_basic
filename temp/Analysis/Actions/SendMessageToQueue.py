
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames;
from Tools.Queue_Handler import Queue_Writer;


class SendMessageToQueue(ActionNode):
    """
    Puts a message into a queue
    """

    def __init__(self, message_queue_settings, coin_symbol, default_node=None):
        """
        Constructor
        """
        super(SendMessageToQueue, self).__init__(default_node=default_node);
        self._set_parameter(name="coin_symbol", parameter=coin_symbol);
        self.__queues = Queue_Writer(message_queue_settings);

    def check(self, data_array):
        message = "Latest data point: " + str(data_array[-1]);
        self.__queues.write_message(self._parameters["coin_symbol"], message);
        return self._children.get(ChildrenNames.default_branch);

    def shutdown(self):
        self.__queues.close_connection();
