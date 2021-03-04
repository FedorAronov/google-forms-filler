import argparse
from os.path import isfile
from time import sleep

from gff.answers import get_response_class
from gff.browsing import load_google_form, submit_google_form
from gff.code_generation import generate_script_template
from gff.exceptions import FormNotFoundException, AuthRequiredException
from gff.utility import print_google_form, generate_default_random_answers, SignalHandler, generate_random_email

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scriptable GoogleForms filling tool.")
    parser.add_argument("url", help="GoogleForms form url")
    parser.add_argument("-i", "--info",
                        action="store_true",
                        help="print form information: questions, descriptions etc.")
    answers_source = parser.add_mutually_exclusive_group()
    answers_source.add_argument("-a", "--auto",
                                action="store_true",
                                help="automatically generate random answers")
    answers_source.add_argument("-us", "--use-script",
                                action="store_true",
                                help="generate answers using existing Python script file")
    answers_source.add_argument("-cs", "--create-script",
                                action="store_true",
                                help="create template answer-generating script file for this form and exit")
    parser.add_argument("-c", "--count",
                        type=int,
                        help="form submissions count. Infinite by default. Used only when --auto flag is set",
                        default=0)
    parser.add_argument("-d", "--delay",
                        type=int,
                        help="delay between form submissions, ms. No delay by default. "
                             "Used only when --auto flag is set",
                        default=0)
    args = parser.parse_args()
    form = None
    try:
        form = load_google_form(args.url)
    except FormNotFoundException:
        print("GoogleForms form was not found at this URL.")
    except AuthRequiredException:
        print("This form has a question with file upload or is private.")
    if not form:
        exit()
    if args.info:
        print_google_form(form)
    if form.requires_login:
        print("This form requires login.")
    elif args.auto:
        print("Selected answers mode: fully random answers.")
        input("Press enter to start form submission...")
        count = 0
        interrupt_handler = SignalHandler()
        interrupt_handler.register_self()
        while args.count == 0 or count < args.count:
            if form.requires_email:
                email = generate_random_email()
            else:
                email = None
            response = submit_google_form(form, generate_default_random_answers(form), email=email)
            if response.status_code == 200:
                count += 1
                print(f"> {count} submissions done.")
            else:
                print(f"Response code {response.status_code} received, stopping.")
                break
            if interrupt_handler.signal_received:
                print(f"Keyboard interrupt requested.")
                break
            sleep(args.delay / 1000)
        print("Finished.")
    elif args.use_script:
        print("Selected answers mode: user script.")
        with open(f"{form.identifier}.py", "r", encoding="UTF-8") as file:
            exec(file.read(), globals())
        answer_provider = FormAnswerProvider(form)
        input("Press enter to start form submission...")
        iteration = 0
        context = answer_provider.get_iteration_context(iteration)
        interrupt_handler = SignalHandler()
        interrupt_handler.register_self()
        while context is not None:
            if form.requires_email:
                email = answer_provider.page0_email(iteration, context)
            else:
                email = None
            answers = []
            for (page_number, page) in enumerate(form.pages):
                for question_number, question in enumerate(page.questions):
                    if get_response_class(question):
                        exec(f'answers.append('
                             f'answer_provider.page{page_number}_question{question_number}(iteration, context)'
                             f')',
                             globals(),
                             locals())
            response = submit_google_form(form, answers, email=email)
            if response.status_code == 200:
                print(f"> {iteration} submissions done.")
            else:
                print(f"Response code {response.status_code} received, stopping.")
                break
            if interrupt_handler.signal_received:
                print(f"Keyboard interrupt requested.")
                break
            iteration += 1
            context = answer_provider.get_iteration_context(iteration)
        print("Finished.")
    elif args.create_script:
        file_name = f"{form.identifier}.py"
        if isfile(file_name):
            print("File", file_name, "already exists.")
        else:
            script = generate_script_template(form)
            with open(f"{form.identifier}.py", "w", encoding="UTF-8") as file:
                file.write(script)
            print("Template script was saved to", file_name)
