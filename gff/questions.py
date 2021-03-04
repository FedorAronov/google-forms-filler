import random
import string
from enum import Enum
from typing import Optional, List

from gff.answers import AnswerTextLine, AnswerTextExtended, AnswerChoiceSingle, AnswerChoiceDropdown, \
    AnswerChoiceMultiple, AnswerScale, AnswerGrid, AnswerGridFlags, AnswerGridFlagsUnique, AnswerDate, \
    AnswerDateWithTime, AnswerDateWithYear, AnswerDateWithTimeAndYear, AnswerTime, AnswerTimeAsDuration, AnswerEmpty
from gff.subquestions import GoogleFormSubquestion


class GoogleFormQuestion(object):
    class Type(Enum):
        TEXT_LINE = 0
        TEXT_EXTENDED = 1
        CHOICE_SINGLE = 2
        CHOICE_DROPDOWN = 3
        CHOICE_MULTIPLE = 4
        SCALE = 5
        GRID = 7
        GRID_FLAGS = -1
        GRID_FLAGS_UNIQUE = -2
        DATE = 9
        DATE_WITH_TIME = -3
        DATE_WITH_YEAR = -4
        DATE_WITH_TIME_AND_YEAR = -5
        TIME = 10
        TIME_AS_DURATION = -6
        COMMENT_TEXT = 6
        COMMENT_IMAGE = 11
        PAGE_SWITCH = 8

        def has_children(self):
            return self not in [
                GoogleFormQuestion.Type.COMMENT_TEXT,
                GoogleFormQuestion.Type.COMMENT_IMAGE,
                GoogleFormQuestion.Type.PAGE_SWITCH
            ]

        def __str__(self):
            return self.name

    def __init__(self,
                 title: str,
                 description: Optional[str],
                 question_type: Type,
                 subquestions: List[GoogleFormSubquestion]):
        self.title = title
        self.description = description
        self.question_type = question_type
        self.subquestions = subquestions

    @property
    def is_required(self) -> bool:
        return any([q.is_required for q in self.subquestions])

    @staticmethod
    def new_instance(data: dict):
        title = data[1]
        description = data[2]
        question_type = GoogleFormQuestion.Type(data[3])
        if question_type.has_children():
            subquestions_data = data[4]
        else:
            subquestions_data = []
        if question_type is GoogleFormQuestion.Type.GRID:
            if len(data) >= 8 and data[7] is not None and data[7] == 0:
                question_type = GoogleFormQuestion.Type.GRID_FLAGS
            elif len(data) >= 9 and data[8] is not None:
                question_type = GoogleFormQuestion.Type.GRID_FLAGS_UNIQUE
        elif question_type is GoogleFormQuestion.Type.DATE:
            subquestion_data = data[4][0]
            if len(subquestion_data) >= 8 and subquestion_data[7] is not None:
                if subquestion_data[7][0] == 1 and subquestion_data[7][1] == 1:
                    question_type = GoogleFormQuestion.Type.DATE_WITH_TIME_AND_YEAR
                elif subquestion_data[7][0] == 1:
                    question_type = GoogleFormQuestion.Type.DATE_WITH_TIME
                elif subquestion_data[7][1] == 1:
                    question_type = GoogleFormQuestion.Type.DATE_WITH_YEAR
        elif question_type is GoogleFormQuestion.Type.TIME:
            subquestion_data = data[4][0]
            if len(subquestion_data) >= 7 and subquestion_data[6] is not None and subquestion_data[6][0] == 1:
                question_type = GoogleFormQuestion.Type.TIME_AS_DURATION
        subquestions = []
        result = GoogleFormQuestion(title, description, question_type, subquestions)
        for subquestion_data in subquestions_data:
            subquestions.append(GoogleFormSubquestion.new_instance(subquestion_data, result))
        return result

    @property
    def default_random_answer(self):
        if self.question_type is GoogleFormQuestion.Type.TEXT_LINE:
            value = ''.join(random.choices(string.ascii_letters + " ", k=random.randint(15, 50)))
            return AnswerTextLine(self, value)
        elif self.question_type is GoogleFormQuestion.Type.TEXT_EXTENDED:
            value = ''.join(random.choices(string.ascii_letters + " \n", k=random.randint(60, 500)))
            return AnswerTextExtended(self, value)
        elif self.question_type is GoogleFormQuestion.Type.CHOICE_SINGLE:
            value = random.choice(self.subquestions[0].choices)
            if value == "":
                value = ''.join(random.choices(string.ascii_letters + " ", k=random.randint(15, 50)))
            return AnswerChoiceSingle(self, value)
        elif self.question_type is GoogleFormQuestion.Type.CHOICE_DROPDOWN:
            value = random.choice(self.subquestions[0].choices)
            return AnswerChoiceDropdown(self, value)
        elif self.question_type is GoogleFormQuestion.Type.CHOICE_MULTIPLE:
            subquestion = self.subquestions[0]
            choices = subquestion.choices
            has_arbitrary_choice = choices[-1] == ""
            values = []
            while len(values) == 0:
                if has_arbitrary_choice:
                    choices = choices[:-1]
                for choice in choices:
                    if random.random() > 0.5:
                        values.append(choice)
                if has_arbitrary_choice:
                    if random.random() > 0.5:
                        values.append(''.join(random.choices(string.ascii_letters + " ", k=random.randint(15, 50))))
            return AnswerChoiceMultiple(self, values)
        elif self.question_type is GoogleFormQuestion.Type.SCALE:
            value = random.choice(self.subquestions[0].choices)
            return AnswerScale(self, value)
        elif self.question_type is GoogleFormQuestion.Type.GRID:
            values = [random.choice(subquestion.choices) for subquestion in self.subquestions]
            return AnswerGrid(self, values)
        elif self.question_type is GoogleFormQuestion.Type.GRID_FLAGS:
            values = []
            for subquestion in self.subquestions:
                subquestion_values = []
                for choice in subquestion.choices:
                    if random.random() > 0.5:
                        subquestion_values.append(choice)
                if subquestion.is_required and len(subquestion_values) == 0:
                    subquestion_values.append(random.choice(subquestion.choices))
                values.append(subquestion_values)
            return AnswerGridFlags(self, values)
        elif self.question_type is GoogleFormQuestion.Type.GRID_FLAGS_UNIQUE:
            values = []
            used_values = []
            for subquestion in self.subquestions:
                subquestion_values = []
                available_choices = [c for c in subquestion.choices if c not in used_values]
                if len(available_choices) == 0 and subquestion.is_required:
                    raise RuntimeError(f"Impossible question. Question: {self.title}")
                elif len(available_choices) > 0:
                    choice = random.choice(available_choices)
                    subquestion_values.append(choice)
                    used_values.append(choice)
                values.append(subquestion_values)
            return AnswerGridFlagsUnique(self, values)
        elif self.question_type is GoogleFormQuestion.Type.DATE:
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            return AnswerDate(self, (month, day))
        elif self.question_type is GoogleFormQuestion.Type.DATE_WITH_TIME:
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            return AnswerDateWithTime(self, (month, day, hour, minute))
        elif self.question_type is GoogleFormQuestion.Type.DATE_WITH_YEAR:
            year = random.randint(1980, 2030)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            return AnswerDateWithYear(self, (year, month, day))
        elif self.question_type is GoogleFormQuestion.Type.DATE_WITH_TIME_AND_YEAR:
            year = random.randint(1980, 2030)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            return AnswerDateWithTimeAndYear(self, (year, month, day, hour, minute))
        elif self.question_type is GoogleFormQuestion.Type.TIME:
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            return AnswerTime(self, (hour, minute))
        elif self.question_type is GoogleFormQuestion.Type.TIME_AS_DURATION:
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            return AnswerTimeAsDuration(self, (hour, minute, second))
        elif self.question_type is GoogleFormQuestion.Type.COMMENT_TEXT:
            return AnswerEmpty()
        elif self.question_type is GoogleFormQuestion.Type.COMMENT_IMAGE:
            return AnswerEmpty()
        else:
            raise RuntimeError(f"Unsupported question type. Question: {self.title}")
