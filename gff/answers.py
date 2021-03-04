from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Type, Dict, Tuple, Optional
    from gff.subquestions import GoogleFormSubquestion
    from gff.questions import GoogleFormQuestion

from collections import OrderedDict
import re


class FormData(object):
    __email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

    def __init__(self, email: Optional[str] = None):
        self.list1: List[Tuple[str, str]] = []
        self.list2: List[Tuple[str, str]] = []
        self.list3: List[Tuple[str, str]] = []
        if email is not None:
            assert FormData.__email_regex.match(email) is not None
        self.email = email

    def accept_chunk(self, chunk: FormDataChunk):
        chunk.visit_form_data(self)

    def build(self) -> Dict[str, str]:
        result = OrderedDict()
        if self.email:
            result["emailAddress"] = self.email
        for (k, v) in self.list1:
            result[k] = v
        for (k, v) in self.list2:
            result[k] = v
        for (k, v) in self.list3:
            result[k] = v
        return result


class FormDataChunk(object):
    def __init__(self, subquestion: GoogleFormSubquestion, has_sentinel: bool):
        self.__identifier = subquestion.identifier
        self.__has_sentinel = has_sentinel
        self.__entries = []

    def __add_entry(self, value: str, suffix: str = ""):
        self.__entries.append((f"entry.{self.__identifier}{suffix}", value))

    def add_simple_entry(self, value: str):
        self.__add_entry(value)

    def add_other_option_entries(self, value: str):
        self.__add_entry(value, ".other_option_response")
        self.__add_entry("__other_option__")

    def add_year_entry(self, value: int):
        self.__add_entry(str(value), "_year")

    def add_month_entry(self, value: int):
        self.__add_entry(str(value), "_month")

    def add_day_entry(self, value: int):
        self.__add_entry(str(value), "_day")

    def add_hour_entry(self, value: int):
        self.__add_entry(str(value), "_hour")

    def add_minute_entry(self, value: int):
        self.__add_entry(str(value), "_minute")

    def add_second_entry(self, value: int):
        self.__add_entry(str(value), "_second")

    def visit_form_data(self, form_data: FormData):
        if self.__has_sentinel:
            form_data.list2.extend(self.__entries)
            form_data.list3.append((f"entry.{self.__identifier}_sentinel", ""))
        else:
            form_data.list1.extend(self.__entries)


class QuestionAnswer(object):
    def __init__(self, question: GoogleFormQuestion, form_data_chunks: List[FormDataChunk]):
        self.question = question
        self.form_data_chunks = form_data_chunks


class AnswerEmpty(QuestionAnswer):
    # noinspection PyTypeChecker
    def __init__(self):
        super(AnswerEmpty, self).__init__(None, [])


class _AnswerSimple(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[str] = None):
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            form_data_chunk.add_simple_entry(value)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerTextLine(_AnswerSimple):
    pass


class AnswerTextExtended(_AnswerSimple):
    pass


class AnswerChoiceSingle(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[str] = None):
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, True)
        if value is not None:
            if value not in subquestion.choices:
                assert "" in subquestion.choices
                form_data_chunk.add_other_option_entries(value)
            else:
                form_data_chunk.add_simple_entry(value)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerChoiceMultiple(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 values: Optional[List[str]] = None):
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, True)
        if values is not None and len(values) > 0:
            for value in values[:-1]:
                assert value in subquestion.choices
                form_data_chunk.add_simple_entry(value)
            value = values[-1]
            if value not in subquestion.choices:
                assert "" in subquestion.choices
                form_data_chunk.add_other_option_entries(value)
            else:
                form_data_chunk.add_simple_entry(value)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerChoiceDropdown(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[str] = None):
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            assert value in subquestion.choices
            form_data_chunk.add_simple_entry(value)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerScale(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[str] = None):
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, True)
        if value is not None:
            assert value in subquestion.choices
            form_data_chunk.add_simple_entry(value)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerGrid(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 values: Optional[List[Optional[str]]] = None):
        if values is None:
            values = [None for _ in range(len(question.subquestions))]
        assert len(question.subquestions) == len(values)
        form_data_chunks = []
        for i in range(len(question.subquestions)):
            subquestion = question.subquestions[i]
            value = values[i]
            form_data_chunk = FormDataChunk(subquestion, True)
            if value is not None:
                assert value in subquestion.choices
                # noinspection PyTypeChecker
                form_data_chunk.add_simple_entry(value)
            else:
                assert not subquestion.is_required
            form_data_chunks.append(form_data_chunk)
        super().__init__(question, form_data_chunks)


class AnswerGridFlags(QuestionAnswer):
    # noinspection PyTypeChecker,PyUnresolvedReferences
    def __init__(self,
                 question: GoogleFormQuestion,
                 values: Optional[List[List[str]]] = None):
        if values is None:
            values = [None for _ in range(len(question.subquestions))]
        assert len(question.subquestions) == len(values)
        form_data_chunks = []
        for i in range(len(question.subquestions)):
            subquestion = question.subquestions[i]
            subquestion_values = values[i]
            form_data_chunk = FormDataChunk(subquestion, True)
            if subquestion_values is not None:
                for j in range(len(subquestion_values)):
                    value = subquestion_values[j]
                    assert value in subquestion.choices
                    assert j == len(subquestion_values) - 1 or value not in subquestion_values[j + 1:]
                    form_data_chunk.add_simple_entry(value)
            else:
                assert not subquestion.is_required
            form_data_chunks.append(form_data_chunk)
        super().__init__(question, form_data_chunks)


class AnswerGridFlagsUnique(QuestionAnswer):
    # noinspection PyTypeChecker,PyUnresolvedReferences
    def __init__(self,
                 question: GoogleFormQuestion,
                 values: Optional[List[List[str]]] = None):
        if values is None:
            values = [None for _ in range(len(question.subquestions))]
        assert len(question.subquestions) == len(values)
        used_values = []
        form_data_chunks = []
        for i in range(len(question.subquestions)):
            subquestion = question.subquestions[i]
            subquestion_values = values[i]
            form_data_chunk = FormDataChunk(subquestion, True)
            if subquestion_values is not None:
                for j in range(len(subquestion_values)):
                    value = subquestion_values[j]
                    assert value in subquestion.choices
                    assert j == len(subquestion_values) - 1 or value not in subquestion_values[j + 1:]
                    assert value not in used_values
                    used_values.append(value)
                    form_data_chunk.add_simple_entry(value)
            else:
                assert not subquestion.is_required
            form_data_chunks.append(form_data_chunk)
        super().__init__(question, form_data_chunks)


class AnswerDate(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[Tuple[int, int]] = None):
        """
        :param value: (Month, Day)
        """
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            (month, day) = value
            assert 1 <= month <= 12
            form_data_chunk.add_month_entry(month)
            assert 1 <= day <= 31  # TODO
            form_data_chunk.add_day_entry(day)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerDateWithTime(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[Tuple[int, int, int, int]] = None):
        """
        :param value: (Month, Day, Hour, Minute)
        """
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            (month, day, hour, minute) = value
            assert 1 <= month <= 12
            form_data_chunk.add_month_entry(month)
            assert 1 <= day <= 31  # TODO
            form_data_chunk.add_day_entry(day)
            assert 0 <= hour < 24
            form_data_chunk.add_hour_entry(hour)
            assert 0 <= minute < 60
            form_data_chunk.add_minute_entry(minute)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerDateWithYear(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[Tuple[int, int, int]] = None):
        """
        :param value: (Year, Month, Day)
        """
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            (year, month, day) = value
            assert 0 < year
            form_data_chunk.add_year_entry(year)
            assert 1 <= month <= 12
            form_data_chunk.add_month_entry(month)
            assert 1 <= day <= 31  # TODO
            form_data_chunk.add_day_entry(day)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerDateWithTimeAndYear(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[Tuple[int, int, int, int, int]] = None):
        """
        :param value: (Year, Month, Day, Hour, Minute)
        """
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            (year, month, day, hour, minute) = value
            assert 0 < year
            form_data_chunk.add_year_entry(year)
            assert 1 <= month <= 12
            form_data_chunk.add_month_entry(month)
            assert 1 <= day <= 31  # TODO
            form_data_chunk.add_day_entry(day)
            assert 0 <= hour < 24
            form_data_chunk.add_hour_entry(hour)
            assert 0 <= minute < 60
            form_data_chunk.add_minute_entry(minute)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerTime(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[Tuple[int, int]] = None):
        """
        :param value: (Hour, Minute)
        """
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            (hour, minute) = value
            assert 0 <= hour < 24
            form_data_chunk.add_hour_entry(hour)
            assert 0 <= minute < 60
            form_data_chunk.add_minute_entry(minute)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


class AnswerTimeAsDuration(QuestionAnswer):
    def __init__(self,
                 question: GoogleFormQuestion,
                 value: Optional[Tuple[int, int, int]] = None):
        """
        :param value: (Hour, Minute, Second)
        """
        assert len(question.subquestions) == 1
        subquestion = question.subquestions[0]
        form_data_chunk = FormDataChunk(subquestion, False)
        if value is not None:
            (hour, minute, second) = value
            assert 0 <= hour < 24
            form_data_chunk.add_hour_entry(hour)
            assert 0 <= minute < 60
            form_data_chunk.add_minute_entry(minute)
            assert 0 <= second < 60
            form_data_chunk.add_second_entry(second)
        else:
            assert not subquestion.is_required
        super().__init__(question, [form_data_chunk])


_type_map = None


def get_response_class(question: GoogleFormQuestion) -> Optional[Type[QuestionAnswer]]:
    global _type_map
    if not _type_map:
        from gff.questions import GoogleFormQuestion
        _type_map = {
            GoogleFormQuestion.Type.TEXT_LINE: AnswerTextLine,
            GoogleFormQuestion.Type.TEXT_EXTENDED: AnswerTextExtended,
            GoogleFormQuestion.Type.CHOICE_SINGLE: AnswerChoiceSingle,
            GoogleFormQuestion.Type.CHOICE_MULTIPLE: AnswerChoiceMultiple,
            GoogleFormQuestion.Type.CHOICE_DROPDOWN: AnswerChoiceDropdown,
            GoogleFormQuestion.Type.SCALE: AnswerScale,
            GoogleFormQuestion.Type.GRID: AnswerGrid,
            GoogleFormQuestion.Type.GRID_FLAGS: AnswerGridFlags,
            GoogleFormQuestion.Type.GRID_FLAGS_UNIQUE: AnswerGridFlagsUnique,
            GoogleFormQuestion.Type.DATE: AnswerDate,
            GoogleFormQuestion.Type.DATE_WITH_TIME: AnswerDateWithTime,
            GoogleFormQuestion.Type.DATE_WITH_YEAR: AnswerDateWithYear,
            GoogleFormQuestion.Type.DATE_WITH_TIME_AND_YEAR: AnswerDateWithTimeAndYear,
            GoogleFormQuestion.Type.TIME: AnswerTime,
            GoogleFormQuestion.Type.TIME_AS_DURATION: AnswerTimeAsDuration
        }
    if question.question_type in _type_map.keys():
        return _type_map[question.question_type]
    else:
        return None
