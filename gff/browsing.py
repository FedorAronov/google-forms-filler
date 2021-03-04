from typing import List, Optional

import requests
from requests import Response
from requests_html import HTMLSession, HTML

from gff.answers import QuestionAnswer, FormData
from gff.exceptions import AuthRequiredException, FormNotFoundException
from gff.form import GoogleForm


def load_google_form(url: str) -> GoogleForm:
    session = HTMLSession()
    response = session.get(url)
    html: HTML = response.html
    html.render(sleep=3)
    form_element = html.xpath("//div/div/form", first=True)
    if form_element is None:
        raise FormNotFoundException()
    submit_url = form_element.attrs["action"]
    print("Form submission URL:", submit_url)
    if submit_url is None:
        raise FormNotFoundException()
    if "https://accounts.google.com/" in submit_url:
        raise AuthRequiredException()
    if not submit_url.endswith("/formResponse"):
        raise FormNotFoundException()
    return GoogleForm.new_instance(submit_url, html)


def submit_google_form(form: GoogleForm,
                       answers: List[QuestionAnswer],
                       page_history: Optional[str] = None,
                       email: Optional[str] = None) -> Response:
    assert not form.requires_email or email is not None
    form_data = FormData(email)
    for answer in answers:
        for form_data_chunk in answer.form_data_chunks:
            form_data.accept_chunk(form_data_chunk)
    data = form_data.build()
    if len(form.pages) > 1:
        if page_history is None:
            page_history = ",".join([str(i) for i in range(len(form.pages))])
        data["pageHistory"] = page_history
    return requests.post(form.submit_url, data=data)
