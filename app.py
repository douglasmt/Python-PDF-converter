# -*- coding: utf-8 -*-
from werkzeug import secure_filename
from work.oauth import client

from flask import Flask, render_template, request, jsonify, url_for, send_from_directory, current_app
import work
import logging
import os
import requests
import clr
import sys

app = Flask('sample', static_folder='static'
            , template_folder='templates'
            )
app.logger.setLevel(logging.DEBUG)
app.config.from_pyfile('config.py')
work.routes.register(app)

user_id = 'admin'
password = '4dm1n!'
server = 'localhost'

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
print("\n---------   INICIO DO PROCESSO    -------------\n")

print("----------------------------------------------\n Iniciando processo em "
      + str(PROJECT_ROOT))

dirDLL                  = os.path.join(PROJECT_ROOT, 'splitPDF\\SplitPDF.dll')
print("---------\n DLL Split PDF: " + str(dirDLL) )

directorySplitGlobal    = os.path.join(PROJECT_ROOT, 'temp\\')
print("---------\n Download PDF: " + str(directorySplitGlobal)
      + "\n----------------------------------------------")


#  Retrieve X-Auth-Token
payload_dictionary = { 'user_id': user_id, 'password': password }

# We are ready to send the request as an HTTP 'PUT' request.
response = requests.put('https://' + server + '/api/v1/session/login',
    json=payload_dictionary, verify = False)

json_response = response.json()
#print(response.json())

if 'X-Auth-Token' in json_response:
    x_auth_token = json_response['X-Auth-Token']
    print('Succeeded.')
    print('')
else:
    print('The login was unsuccessful.')
    print(json_response['error']['message'])

# Authorize the API request by sending the X-Auth-Token that is
# retrieved when logging in, as a header.

headers = {'X-Auth-Token': x_auth_token}


@app.route('/')
def index():
    app.logger.debug('index()')
    return 'Hello, World!'

#Split PDF
@app.route('/peticionamento-eletronico', methods=['GET', 'POST'])
def peticionamento_eletronico():

    if request.method == 'GET':
        # Receive context, and make a POST request to same endpoint with context
        #return render_template('convert_to_pdf.html')
        return render_template('peticionamento_eletronico.html')
    else:
        # When method=POST...

        doc_id = request.json.get('id')
        print("\n----------------------------------------------\nDocument id: " + doc_id)

        doc_extension = request.json.get('extension')
        print("Document extension: " + doc_extension)

        doc_name = request.json.get('name')
        print("Document name: " + doc_name)

        tamanho = request.json.get('tamanho')
        print("Document name: " + str(tamanho))

        print("------- \n Splitting PDF para " + str(tamanho)
              + "\n----------------------------------------------")
        tamanhoAceitoTribunal = tamanho * 1000

        pet_elet_download_split_remove(tamanhoAceitoTribunal, doc_id, doc_name)
    
       
    return render_template('peticionamento_eletronico.html')

# PETICIONAMENTO  para cada tamanho escolhido
def pet_elet_download_split_remove(tamanhoAceitoTribunal, doc_id, doc_name):
    
    print("\n----- pet_elet_download_split_remove ---\n" + doc_id)
    file_PDF = peticionamento_download(doc_id, doc_name) 
    print("\n----------------------------------------------")
    
    clr.AddReference(dirDLL)
    from SplitPDFPython import MyCSCommand
    my_instance = MyCSCommand()

    print("\n----------------------------------------------")    
    print(my_instance.PDFSplit(file_PDF, tamanhoAceitoTribunal, doc_name))

    print("\n----------------------------------------------\n")
    print("Removendo: " + file_PDF)
    os.remove(file_PDF)
    print("\n---------   FINAL DO PROCESSO    -------------\n")
    
    sys.stdout.flush()


# DOWNLOAD para cada arquivo
def peticionamento_download(document_id, name):
    
    response = requests.get('https://' + server + '/api/v1/documents/' + document_id +
                            '/download',headers=headers, verify = False)

    print("\n----------  peticionamento_download  -----------")
    file_PDF = directorySplitGlobal + document_id + ' - ' + name
    print(file_PDF)
    
    # Check if the API request was successful
    if response.status_code == 200:                          
        downloaded_file = open(file_PDF , 'wb')
        downloaded_file.write(response.content)
        downloaded_file.close()
        print('The file was downloaded successfully.')
        return file_PDF

    else:
        # API request failed. Print the error message.
        print('Task failed.')
        json_response = response.json()
        print(json_response['error']['message'])



### TESTES ####
@app.route('/matter-view')
def matter_view():
    return render_template('matter_view.html')

@app.route('/recent')
@work.token.required
def recent_documents():
    me = work.api.users.me()
    recent = work.api.documents.recent()
    return render_template('recent_documents.html', user=me, recent=recent)

#teste para converter pdf
@app.route('/convert-to-pdf', methods=['GET', 'POST'])
#@work.token.required
def convert_to_pdf():
    if request.method == 'GET':
        # Receive context, and make a POST request to same endpoint with context
        return render_template('convert_to_pdf.html')
    else:
        # When method=POST...
                
        doc_id = request.json.get('id')
        print("Document id: " + doc_id)
        #document_id = doc_id

        doc_extension = request.json.get('extension')
        print("Document extension: " + doc_extension)

        doc_name = request.json.get('name')
        print("Document name: " + doc_name)


        print("------- \nSplitting PDF para 2048 * 1000:")
        tamanhoAceitoTribunal = 6144 * 1000

        pet_elet_download_split_remove(tamanhoAceitoTribunal, doc_id, doc_name)


        '''doc_name = request.json.get('name')
        print("Document name: " + doc_name)'''

        '''response = requests.get('https://' + server + '/api/v1/documents/'
                                + doc_id +
                                '/download',headers=headers, verify = False)
        path = 'temp/%s.%s' % (doc_id, extension)
        work.api.documents.download(doc_id, path)
        # convert to pdf now!!
        # ...cheat null implementation...
        # assuming it is done...
        pdf_path = 'temp/converted.pdf'
        r = work.api.documents.new_version(doc_id, pdf_path)
        return jsonify(r)'''



if __name__ == '__main__':
    os.environ['DEBUG'] = "1"
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    app.run('localhost', use_reloader=True,
            #'LUIZ',
            debug=True )        
