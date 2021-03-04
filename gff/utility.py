import random
import signal
import string
from typing import List, Optional

from gff.form import GoogleForm
from gff.answers import QuestionAnswer


class SignalHandler:
    def __init__(self):
        self.signal_received = False

    def handle_signal_received(self):
        self.signal_received = True

    @property
    def handler_function(self):
        return lambda sig, frame: self.handle_signal_received()

    def register_self(self, sig=signal.SIGINT):
        signal.signal(sig, self.handler_function)


def shorten_string(value: Optional[str], max_length: int = 50) -> Optional[str]:
    if value and len(value) > max_length:
        value = value[:max_length] + "..."
    return value


def _clean_string(value: Optional[str]) -> Optional[str]:
    if value:
        return value.replace("\n", "")
    return value


def print_google_form(form: GoogleForm):
    print("*** General info ***")
    print("Title:         ", form.title)
    print("File name:     ", form.file_name)
    print("Description:   ", shorten_string(_clean_string(form.description)))
    print("Requires email:", form.requires_email)
    print("Pages count:   ", len(form.pages))
    print("********************")
    for page_number, page in enumerate(form.pages):
        print(f"*** Page №{page_number + 1} ***")
        print("Title:          ", page.title)
        print("Description:    ", shorten_string(_clean_string(page.description)))
        print("Questions count:", len(page.questions))
        for question_number, question in enumerate(page.questions):
            print("*")
            print(f"* Question №{question_number + 1}")
            print("* Type:       ", question.question_type)
            print("* Title:      ", shorten_string(_clean_string(question.title)))
            print("* Description:", shorten_string(_clean_string(question.description)))
            print("* Is required:", question.is_required)
            if len(question.subquestions) == 1:
                if len(question.subquestions[0].choices) > 0:
                    print("* Choices:")
                    for choice in question.subquestions[0].choices:
                        if choice != "":
                            print(">", choice)
                        else:
                            print(">", "'Other'")
            print("*")
        print("********************")


def generate_random_email() -> str:
    symbols = random.choices(string.ascii_lowercase + string.digits, k=random.randint(3, 10))
    return "".join(symbols) + "@gmail.com"


def generate_default_random_answers(form: GoogleForm) -> List[QuestionAnswer]:
    answers = []
    for page in form.pages:
        for question in page.questions:
            answers.append(question.default_random_answer)
    return answers
