from abc import abstractmethod, ABC
from typing import Dict, List, Optional

from gff.answers import get_response_class
from gff.form import GoogleForm
from gff.utility import shorten_string


def _tabulate(text: str, count: int = 1):
    tabs = "\t" * count
    return tabs + tabs.join(text.splitlines(keepends=True))


def _format_doc(doc: Optional[str]):
    if doc:
        return _tabulate(f'"""\n{doc}\n"""') + "\n"
    else:
        return ""


class _ClassPart(ABC):
    @abstractmethod
    def to_string(self) -> str:
        raise NotImplemented


class _Method(_ClassPart):
    def __init__(self, name: str,
                 doc: Optional[str] = None,
                 args: Dict[str, str] = None,
                 return_type: Optional[str] = None,
                 code: Optional[str] = None):
        self.name = name
        self.doc = doc
        self.args = args
        self.return_type = return_type
        if code:
            self.code = code
        else:
            self.code = "pass"

    def to_string(self):
        if self.args:
            args_str = "self, " + ", ".join([f"{k}: {v}" for (k, v) in self.args.items()])
        else:
            args_str = "self"
        if self.return_type:
            return_type_str = f" -> {self.return_type}"
        else:
            return_type_str = ""
        doc_str = _format_doc(self.doc)
        result = \
            f"def {self.name}({args_str}){return_type_str}:\n" + \
            doc_str + \
            _tabulate(self.code) + \
            "\n" * 2
        return result


class _Comment(_ClassPart):
    def __init__(self, text: str, trailing_newlines: int = 0):
        self.text = text
        self.trailing_newlines = trailing_newlines

    def to_string(self):
        result = "".join([f"# {line}" for line in self.text.splitlines(keepends=True)]) + \
                 "\n" * (self.trailing_newlines + 1)
        return result


class _Class:
    def __init__(self, name: str, doc: str, parts: List[_Method]):
        self.name = name
        self.doc = doc
        self.parts = parts

    def build_string(self):
        result = f"class {self.name}:\n"
        if self.doc:
            doc_str = _format_doc(self.doc)
            result += doc_str + "\n"
        for part in self.parts:
            result += _tabulate(part.to_string())
        return result


def generate_script_template(form: GoogleForm) -> str:
    stars = "*" * 114
    parts = [
        _Method("__init__",
                ':param form: Google form instance',
                {"form": "GoogleForm"},
                code="self.form = form"),
        _Method("get_iteration_context",
                "Called before each new iteration.\n"
                ":return dict: Arbitrary dictionary, or None to stop iteration.",
                {"iteration": "int"},
                "Optional[dict]",
                "return {}")
    ]
    if form.requires_email:
        parts.append(
            _Method("page0_email",
                    "Email.\n"
                    ":return str: Valid email address.",
                    {"iteration": "int", "context": "dict"},
                    "str",
                    "return generate_random_email()"))
    for (page_number, page) in enumerate(form.pages):
        parts.append(
            _Comment(stars + f'\nPage №{page_number}.\nTitle: "{shorten_string(page.title, 90)}".\n' + stars, 1))
        for (question_number, question) in enumerate(page.questions):
            return_type = get_response_class(question)
            if return_type:
                return_type = return_type.__name__
                if not question.is_required:
                    return_type = f"Union[{return_type}, AnswerEmpty]"
                parts.append(_Method(f"page{page_number}_question{question_number}",
                                     f'Question title: "{shorten_string(question.title, 90)}"',
                                     {"iteration": "int", "context": "dict"},
                                     return_type,
                                     f"question = self.form.pages[{page_number}].questions[{question_number}]\n"
                                     f"return question.default_random_answer"))
    imports_str = \
        "from gff.answers import *\n" + \
        "from gff.form import GoogleForm\n" \
        "from gff.questions import GoogleFormQuestion\n" \
        "from gff.utility import generate_random_email\n" \
        "\n" \
        "from typing import Optional, Union\n"
    inspection_comment = "# noinspection PyMethodMayBeStatic,PyUnusedLocal\n"
    class_doc = f"Form information\n" \
                f"Title:            {shorten_string(form.title)}\n" \
                f"Description:      {shorten_string(form.description)}\n" \
                f"File name:        {shorten_string(form.file_name)}\n" \
                f"Requires email:   {form.requires_email}\n" \
                f"Number of pages:  {len(form.pages)}"
    return imports_str + "\n" * 2 + inspection_comment + _Class("FormAnswerSupplier", class_doc, parts).build_string()
