# GoogleFormsFiller
Scriptable GoogleForms filling tool.

## Usage
```console
~> python -m gff -h
usage: __main__.py [-h] [-i] [-a | -us | -cs] [-c COUNT] [-d DELAY] url

Scriptable GoogleForms filling tool.

positional arguments:
  url                   GoogleForms form url

optional arguments:
  -h, --help            show this help message and exit
  -i, --info            print form information: questions, descriptions etc.
  -a, --auto            automatically generate random answers
  -us, --use-script     generate answers using existing Python script file
  -cs, --create-script  create template answer-generating script file for this form and exit
  -c COUNT, --count COUNT
                        form submissions count. 
                        Infinite by default. 
                        Used only when --auto flag is set
  -d DELAY, --delay DELAY
                        delay between form submissions, ms. 
                        No delay by default. 
                        Used only when --auto flag is set
```

## Examples
### Form info
Consider such form:
![Example form](https://i.imgur.com/zgs4Qn6.png)

Output:
```console
~> python -m gff https://forms.gle/TH6djhpxYLVuJaVR9 -i
Form submission URL: https://docs.google.com/forms/d/e/1FAIpQLSeGc67eOIK51V2idSaF-wWIUWTqavNj93uzJCI70PaTXnhy1w/formResponse
*** General info ***
Title:          Test form
File name:      New form
Description:    Description
Requires email: True
Pages count:    1
********************
*** Page №1 ***
Title:           Test form
Description:     Description
Questions count: 1
*
* Question №1
* Type:        CHOICE_SINGLE
* Title:       First question
* Description: None
* Is required: True
* Choices:
> 1
> 2
> 3
*
********************
```
### Answer generation
```console
~> python -m gff https://forms.gle/TH6djhpxYLVuJaVR9 -a -c 30
Form submission URL: https://docs.google.com/forms/d/e/1FAIpQLSeGc67eOIK51V2idSaF-wWIUWTqavNj93uzJCI70PaTXnhy1w/formResponse
Selected answers mode: fully random answers.
Press enter to start form submission...
> 1 submissions done.
> 2 submissions done.
> 3 submissions done.
...
> 30 submissions done.
Finished.
```
Result:
![Responses](https://i.imgur.com/5pEdDot.png)
### Custom answers script
```console
~>python -m gff https://forms.gle/TH6djhpxYLVuJaVR9 -cs
Form submission URL: https://docs.google.com/forms/d/e/1FAIpQLSeGc67eOIK51V2idSaF-wWIUWTqavNj93uzJCI70PaTXnhy1w/formResponse
Template script was saved to 1FAIpQLSeGc67eOIK51V2idSaF-wWIUWTqavNj93uzJCI70PaTXnhy1w.py
```
Result ==(1FAIpQLSeGc67eOIK51V2idSaF-wWIUWTqavNj93uzJCI70PaTXnhy1w.py)==:
```python
from gff.answers import *
from gff.form import GoogleForm
from gff.questions import GoogleFormQuestion
from gff.utility import generate_random_email

from typing import Optional, Union


# noinspection PyMethodMayBeStatic,PyUnusedLocal
class FormAnswerSupplier:
	"""
	Form information
	Title:            Test form
	Description:      Description
	File name:        New form
	Requires email:   True
	Number of pages:  1
	"""

	def __init__(self, form: GoogleForm):
		"""
		:param form: Google form instance
		"""
		self.form = form
	
	def get_iteration_context(self, iteration: int) -> Optional[dict]:
		"""
		Called before each new iteration.
		:return dict: Arbitrary dictionary, or None to stop iteration.
		"""
		return {}
	
	def page0_email(self, iteration: int, context: dict) -> str:
		"""
		Email.
		:return str: Valid email address.
		"""
		return generate_random_email()
	
	# ******************************************************************************************************************
	# Page №0.
	# Title: "Test form".
	# ******************************************************************************************************************
	
	def page0_question0(self, iteration: int, context: dict) -> AnswerChoiceSingle:
		"""
		Question title: "First question"
		"""
		question = self.form.pages[0].questions[0]
		return question.default_random_answer

```
For each question, answer of the corresponding type must be returned, or _AnswerEmpty_, if this question is not required.