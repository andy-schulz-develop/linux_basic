
from Analysis.Actions.ActionNode import ActionNode, ChildrenNames


class PrintToScreenAction(ActionNode):
    """
    Just prints the latest data point on the screen
    """

    def __init__(self, default_node: ActionNode = None):
        """
        Constructor
        """
        super(PrintToScreenAction, self).__init__(default_node=default_node);

    def check(self, data_array: list):
        print("Latest data point: " + str(data_array[-1]));
        return self._children.get(ChildrenNames.default_branch);
