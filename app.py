from random import randrange
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import fitz
import json
import os
import time
from openai import OpenAI

assistant_API = ""

client = OpenAI(api_key = os.environ.get("OPENAI_API_KEY"))
assistant = client.beta.assistants.retrieve(assistant_API)

app = Flask(__name__)
UPLOAD_FOLDER = './static/uploads/'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

socketio = SocketIO(app)

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_files():

    results = []

    dutch = False

    files = request.files.getlist('file')
    if files[0].filename == 'ABN Offer.pdf':
        print("ABN OFFER NOW")
        dutch = True

    epparg_standards = ["Equity release products shall be lifetime products. The customers shall be able to live in their main homes for their whole life to enjoy and maintain.", "If the customer is residing on the property and upholding its contractual obligations, the provider (which term henceforth in this document includes any creditor to which the loan is subsequently transferred) has the right to require repayment of the outstanding loan, rolled up interest and costs due, only upon the customer’s death or a move into permanent long-term care.","When an event occurs, which makes the loan due for repayment, the customer or the customer’s estate shall be given a reasonable time to arrange for the repayment, which includes time for estate inventory proceedings and/or sale of the property for the repayment of the amounts due with the proceeds. Unless the property is to be sold at a public auction, the provider shall have a contractual right to control that the property is professionally sold at market conditions.","If on the property’s sale on market conditions, the sales proceeds are lower than the amount due, and provided that the customer is not in breach of any substantial contractual obligations, the provider will not expect the customer or the customer’s estate or heirs to make up the shortfall with other assets. This commitment shall as a minimum be applied when the property is sold following the customer’s death or permanent move to long term care.","Providers should allow customers to transfer the loan to another suitable property, which meets the providers’ then lending conditions and criteria.","Early redemption of the loans should be permitted. Providers should at the outset make clear the likely cost impact to the customer for such redemption and ensure transparency of costs.","Product providers may offer a range of terms, including interest served, rolled up, fixed for life or a term, or variable. In case of variable interest customers should preferably be offered an option to have an interest rate cap and in any case be informed of the impact of not having such a cap.","In the pre-sales information pack, the impact of compounded interest shall be shown – in different interest rate scenarios if required – showing the growth of the total debt over time. A comparison between these calculations and the home-value development in different house price index scenarios shall also be included, showing estimated development of the customer’s net equity.","The providers are required to ensure that all information from the provider to customers and the contracting process are done by competent, knowledgeable and duly authorized persons.","The providers will require that a checklist has been completed before contract signing, showing that the customer has received the required relevant information. The checklist shall be signed by both the customer and the informer and a copy given to the provider and the customer."]
        
    for i, epparg in enumerate(epparg_standards):
        # if 1 == 1:
        #     break;

        print(epparg)

        thread = client.beta.threads.create()

        content = "EPPARG STANDARD """ + str(i + 1) + ":"

        content += "\"" + epparg + "\""
        
        content += """Check the EPPARG standard above against all of the uploaded documents for compliance. Find all of the evidence then make a final analysis of whether the standard is met or not.
        
        When you respond can you return your answer in JSON format with the following format: 
        
        {
            "standard_no": ,
            "compliance": "", # met, not met
            "evidence": ["", ""], # actual text from the source, do not return a link only put the actual text, that shows the compliance, if there's links to other paragraphs etc then include those too (or 'no text found')
            "source": ["", ""], # which document you found the evidence in, only the name of the file, not the id (or 'none' if you didn't find any evidence)
            "page_no": [5, 4], # the page number the evidence is found on, a page number for each source (or 'none' if you didn't find any evidence)
            "analysis": "" # your final analysis
        }

        If you find multiple answers use the one where the standard is met, the most evidential one if there is one, and ignore any others.

        Your answer should only be a valid JSON object, nothing else. Do not include comments in your JSON, only the data itself. Remove any hidden characters and make sure it's compliant with UTF-8."""

        message = client.beta.threads.messages.create(
            thread_id = thread.id,
            role = "user",
            content = content
        )

        run = client.beta.threads.runs.create(
            thread_id = thread.id,
            assistant_id = assistant.id
        )

        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            time.sleep(3)

        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )

        # print("\n\nRAW MESSAGE " + str(i+1) + ": " + messages.data[0].content[0].text.value)
        timer = randrange(70,140) / 100
        time.sleep(timer)
        if dutch:
            socketio.emit('progress', {'progressText': 'EPPARG Standaard ' + str(i + 1) + ' controle voltooid.', "progress": str(10 * (i + 1)) })
        else:
            socketio.emit('progress', {'progressText': 'EPPARG Standard ' + str(i + 1) + ' check complete.', "progress": str(10 * (i + 1)) })

        result = json.loads(messages.data[0].content[0].text.value.replace("```json", '').replace("```", ''))

        # print("\n\nRESULT " + str(i+1) + ": " + str(result))
    
        results.append(result)

        # if i == 2:
        #     break;
    

    print(results)

    socketio.emit('result', { 'texts': results, 'dutch': dutch })

    return ""

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify(error="No selected files"), 400
    
    texts = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = file.filename
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            try:
                # Extract text from the uploaded PDF
                text = extract_text_from_pdf(file_path)
                socketio.emit('progress', {'progressText': 'Extracted text from PDF', "progress": 5})
                texts += text
                print(texts)
                os.remove(file_path)  # Remove the file after extraction 
            except Exception as e:
                return jsonify(error=str(e)), 500
        else:
            return jsonify(error="File type not allowed"), 400
        
        texts = lfgo(texts)

        # print(texts)
        socketio.emit('progress', {'progressText': 'Analysis complete.', "progress": 100 })

    
    return jsonify(texts=texts)

def extract_text_from_pdf(pdf_path):
    text = []
    with fitz.open(pdf_path) as doc:
        # counter = 0
        localtext = ""
        for page in doc:
            localtext += page.get_text()
            # if counter % 20 == 0 or counter == len(doc) - 1:
        text.append(localtext)
                # localtext = ""
            # counter += 1
    return text

def lfgo(texts):   
    results = []

    for i, res in enumerate(texts):
        text = "This is the ten EPPARG standards (Do not use them in your response):\n"
        with open('./static/texts/epparg.txt', 'r') as f:
            text += f.read()
        text += "Do not use the above standards in your response - they are only for your reference. Do not put any of this text in the 'relevant_text_from_offer' field under any circumstances."
        text += "\n\n"
        text += "<offer>"
        text += res
        text += "</offer>"
        text += "\n\n"
        text += "Does the offer text confirm that the ten standards have been complied with?\n\n"
        text += "Give your answer in the form of only an array of JSON objects that takes this shape:\n\n"
        text += "[{ \"standard\": 1, \"met\": true, \"relevant_text_from_offer\": \"blah\"}]"
        text += "\n\n"
        text += "Do not use the EPPARG standards in your response. Only include text in the 'relevant_text_from_offer' field found within the <offer> tags."
        text += "\n\n"
        text += "Do not inclue anything in your response other than the JSON itself."

        # if i < len(texts) - 1:
        socketio.emit('progress', {'progressText': 'Analysing PDF - pages: ' + str(1 + (i * 5)) + ' to ' + str(5 + (i * 5)), "progress": 5 + (20 * i)})
        # else:
        #     socketio.emit('progress', {'progressText': 'Analysing PDF - pages: ' + str(1 + (i * 5)) + ' to ' + str(len(texts) * 5 + 5), "progress": 5 + (20 * i)})

        completion = client.chat.completions.create(
                        model="gpt-4-1106-preview",
                        messages=[
                            {"role": "system", "content": "You are an expert at analysing mortgage offers. All your responses are JSON only. Do not include the EPPARG Standards in your response."},
                            {"role": "user", "content": text}
                        ],
                        temperature=0,
                        max_tokens=2000,
                        top_p=0.1,
                        frequency_penalty=0,
                        presence_penalty=0
                    )
        
        result = completion.choices[0].message.content

        print(result)

        results = update_results(results, json.loads(result))

    return results

def update_results(results, result):
    if not results:
        results.extend(result)
    else:
        for i, existing_item in enumerate(results):
            new_item = result[i]
            print(new_item)
            print("---------")
            print(existing_item)
            if new_item and existing_item.get('met') is False and new_item.get('met') is True:
                results[i] = new_item
            if existing_item.get('met') is True and new_item.get('met') is True:
                res = standard_check(existing_item, new_item)
                if res == "2":
                    results[i] = new_item
    return results

def standard_check(existing_item, new_item):
    epparg_standards = ["Equity release products shall be lifetime products. The customers shall be able to live in their main homes for their whole life to enjoy and maintain.", "If the customer is residing on the property and upholding its contractual obligations, the provider (which term henceforth in this document includes any creditor to which the loan is subsequently transferred) has the right to require repayment of the outstanding loan, rolled up interest and costs due, only upon the customer’s death or a move into permanent long-term care.","When an event occurs, which makes the loan due for repayment, the customer or the customer’s estate shall be given a reasonable time to arrange for the repayment, which includes time for estate inventory proceedings and/or sale of the property for the repayment of the amounts due with the proceeds. Unless the property is to be sold at a public auction, the provider shall have a contractual right to control that the property is professionally sold at market conditions.","If on the property’s sale on market conditions, the sales proceeds are lower than the amount due, and provided that the customer is not in breach of any substantial contractual obligations, the provider will not expect the customer or the customer’s estate or heirs to make up the shortfall with other assets. This commitment shall as a minimum be applied when the property is sold following the customer’s death or permanent move to long term care.","Providers should allow customers to transfer the loan to another suitable property, which meets the providers’ then lending conditions and criteria.","Early redemption of the loans should be permitted. Providers should at the outset make clear the likely cost impact to the customer for such redemption and ensure transparency of costs.","Product providers may offer a range of terms, including interest served, rolled up, fixed for life or a term, or variable. In case of variable interest customers should preferably be offered an option to have an interest rate cap and in any case be informed of the impact of not having such a cap.","In the pre-sales information pack, the impact of compounded interest shall be shown – in different interest rate scenarios if required – showing the growth of the total debt over time. A comparison between these calculations and the home-value development in different house price index scenarios shall also be included, showing estimated development of the customer’s net equity.","The providers are required to ensure that all information from the provider to customers and the contracting process are done by competent, knowledgeable and duly authorized persons.","The providers will require that a checklist has been completed before contract signing, showing that the customer has received the required relevant information. The checklist shall be signed by both the customer and the informer and a copy given to the provider and the customer."]
    

    text = "Given this epparg standard:\n\n"
    text += epparg_standards[existing_item.get('standard') - 1]
    text += "\n\n"
    text += "And two relevant texts from the offer:\n\n"
    text += existing_item.get('relevant_text_from_offer') + "\n\n"
    text += new_item.get('relevant_text_from_offer') + "\n\n" 
    text += "Which of the two texts is more relevant to the standard?\n\n"
    text += "Give your answer as a number only, either '1' or '2' ONLY do not talk about anything else."

    completion = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert at analysing mortgage offers. All your responses are either '1' or '2'."},
                            {"role": "user", "content": text}
                        ],
                        temperature=0,
                        max_tokens=20,
                        top_p=0,
                        frequency_penalty=0,
                        presence_penalty=0
                    )
    
    result = completion.choices[0].message.content

    print("RESULT: " + result)

    return result

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)