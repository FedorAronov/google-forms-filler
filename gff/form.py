import json
from requests_html import HTML, Element
from typing import List

from gff.exceptions import FormNotFoundException
from gff.page import GoogleFormPage
from gff.questions import GoogleFormQuestion


class GoogleForm(object):
    def __init__(self,
                 submit_url: str,
                 title: str,
                 description: str,
                 file_name: str,
                 requires_login: bool,
                 requires_email: bool,
                 pages: List[GoogleFormPage]):
        self.submit_url = submit_url
        self.title = title
        self.description = description
        self.file_name = file_name
        self.requires_login = requires_login
        self.requires_email = requires_email
        self.pages = pages

    @property
    def identifier(self) -> str:
        return self.submit_url.split("/")[-2]

    @staticmethod
    def __parse_form_definition_script(element: Element) -> dict:
        start = "var FB_PUBLIC_LOAD_DATA_ = "
        text = element.text
        index1 = text.index(start) + len(start)
        index2 = -2
        return json.loads(text[index1:index2])

    @staticmethod
    def new_instance(submit_url: str, html: HTML):
        form_definition_script = \
            html.xpath('//script[text()[contains(.,"FB_PUBLIC_LOAD_DATA_")]]', first=True)
        if not form_definition_script:
            raise FormNotFoundException()
        form_definition = \
            GoogleForm.__parse_form_definition_script(form_definition_script)
        title = form_definition[1][8]
        description = form_definition[1][0]
        file_name = form_definition[3]
        if form_definition[1][10] is not None:
            requires_login = bool(form_definition[1][10][1])
            requires_email = bool(form_definition[1][10][4])
        else:
            requires_login = False
            requires_email = False
        questions_data = form_definition[1][1]
        pages = []
        page_title = title
        page_description = description
        page_questions = []
        for question_data in questions_data:
            question = GoogleFormQuestion.new_instance(question_data)
            if question.question_type is GoogleFormQuestion.Type.PAGE_SWITCH:
                pages.append(GoogleFormPage(page_title, page_description, page_questions))
                page_title = question.title
                page_description = question.description
                page_questions = []
            else:
                page_questions.append(question)
        pages.append(GoogleFormPage(page_title, page_description, page_questions))
        return GoogleForm(submit_url, title, description, file_name, requires_login, requires_email, pages)
