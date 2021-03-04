from typing import List


class GoogleFormSubquestion(object):
    def __init__(self,
                 parent,
                 identifier: int,
                 is_required: bool,
                 choices: List[str]):
        self.parent = parent
        self.identifier = identifier
        self.is_required = is_required
        self.choices = choices

    @staticmethod
    def new_instance(data: dict, parent):
        identifier = data[0]
        is_required = bool(data[2])
        choices = []
        if data[1] is not None:
            for choice in data[1]:
                choices.append(choice[0])
        return GoogleFormSubquestion(parent, identifier, is_required, choices)
