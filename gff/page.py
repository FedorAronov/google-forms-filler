from gff.questions import GoogleFormQuestion
from typing import List


class GoogleFormPage(object):
    def __init__(self, title: str, description: str, questions: List[GoogleFormQuestion]):
        self.title = title
        self.description = description
        self.questions = questions
