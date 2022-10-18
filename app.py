import PyPDF2
from  flask import Flask, request, jsonify, Response, redirect, url_for, render_template
import uuid
import asyncio
import os, time
from os import listdir
from os.path import isfile, join
import glob
import pandas as pd
import datetime
import subprocess
#for opening excel
from pathlib import Path

app = Flask(__name__)
working_path = "/Users/Manikanth/Desktop/DirectBill/home/direct_bill_admin/Documents/projects/DirectBill/DirectBill/"
app.config["FILE_UPLOADS"] = working_path

@app.route('/')
def index():
   return render_template('health.html')

@app.route("/upload/<string:uid>", methods=['POST','GET'])
def upload(uid):
   if request.method == "POST":
      print(uid)
      if request.files:
         uploaded_file = request.files['file']
         filename = uploaded_file.filename
         uploaded_file.save(os.path.join(app.config["FILE_UPLOADS"],filename))

         output_dir = working_path+"output/"
            
         if not os.path.exists(output_dir):
            os.mkdir(output_dir)
            
         if not os.path.exists(output_dir+filename):
            os.replace(working_path+filename,output_dir+filename)
         else:
            os.remove(working_path+filename)
               
         #Get the list of pdf files from output directory
         output_files = [f for f in listdir(output_dir) if isfile(join(output_dir, f)) and f.endswith((".pdf",".xlsx",".xls"))]
         print(output_files)
         
         if len(output_files) != 0:
            isDirectory = os.path.exists(output_dir+"/"+uid)
            if not isDirectory:
               os.mkdir(output_dir+"/"+uid) 
            old_file_name = output_dir+filename
            new_file_name = output_dir+ uid +"/"+filename
            os.rename(old_file_name, new_file_name)
            print("File renamed!")

         #return 'File '+filename+' is uploaded successfully'
         res_body = {'currentDT': datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
         'request_method': request.method,
         'path_info': request.path,
         'http_user_agent': request.headers.get('User-Agent'),
         'ip_addr': request.remote_addr,
         'record_id': uid,
         'file_name': filename}
   #return jsonify(res_body)      
   return render_template("log.html",res_body=res_body)

@app.route("/health", methods=['POST','GET'])
async def health():
   if request.method == "POST":
      condition = request.form.get('condition')
      print(condition)
      if condition == "Dead":
         os.system("taskkill /f /im python.exe")
      elif condition == "Alive":
         operation = "OK"
      return render_template("health.html",operation=operation)
   await asyncio.sleep(1)

@app.route("/uid", methods=['POST','GET'])
def uid():
   if request.method == "GET":
      id = str(uuid.uuid4().int)
      print("The random id using uuid4() is : ",end="") 
      print(id)
      #timecomponent = uuid.uuid4().node
      return render_template('upload.html',id=id)

@app.route("/is_done", methods=['POST','GET'])
def is_done():
   if request.method == "POST":
      uid = request.form.get('uid')
      completion_status = False
      already_completed = os.listdir(working_path+"output/")
      if uid in already_completed:
         completion_status = True
      if completion_status == True:
         response = "Already Completed uploading with uuid"
      else:
         response = "Not Completed uploading with uuid! possibly file type is not pdf or xlsx/xls"
   return Response(response,status=201,mimetype='application/json')

@app.route("/openpdf/<string:uid>/<string:fname>",methods=['POST','GET'])
def openpdf(uid,fname):
   if request.method == "GET":
      path = working_path+"output/"+uid+"/"+fname
      subprocess.Popen([path], shell=True)
      return Response(fname+" is opened",status=201,mimetype='application/json')

@app.route("/openexcel/<string:uid>/<string:fname>",methods=['POST','GET'])
def openexcel(uid,fname):
   if request.method == "GET":
      location = working_path+"output/"+uid+"/"+fname
      # opening EXCEL through Code
					#local path in dir
      absolutePath = Path(location).resolve()
      os.system(f'start excel.exe "{absolutePath}"')
      return Response(fname+" is opened",status=201,mimetype='application/json')

@app.route("/id/<string:id>",methods=['POST','GET'])
def id(id):
   if request.method == "GET":
      output_dir = working_path+"output/"+id
      print('inside id')
      print(output_dir)
      files=[]
      
      for file in get_files(output_dir):
         files.append(file)
         print(files)      
      files=get_files(output_dir)
      res = {'id':id,
            'files':files}
   return render_template('id.html', res=res)

@app.route("/retrieve/<string:uid>/<string:filename>", methods=['POST','GET'])
def retrieve(uid,filename):
   if request.method == "POST": 
      print("inside retrieve")
      print(filename)
      staging_directory = working_path+"output/"
      now = time.time()
      # this is garbage collection (deletes files that are older than 7 days)
      for file in os.listdir(staging_directory):
         if os.path.getmtime(os.path.join(staging_directory, file)) < now - 7 * 86400:
            if os.path.isfile(os.path.join(staging_directory, file)):
               print(file)
               os.remove(os.path.join(staging_directory, file))
      
      if filename.endswith('.xlsx'):
         #_files = []
         #text = {}
         # read all the files with extension .xlsx i.e. excel 
         output_files = glob.glob(staging_directory+uid+"/*.xlsx")
         print('File names:', output_files)      
         for file in output_files:
            # reading excel files
            print("Reading file = ",file)
            #_files.append(pd.read_excel(file))
            #text[file] = pd.read_excel(file)
            print(pd.read_excel(file))

         # load excel file using pandas
         f = pd.ExcelFile(file)

         #define an empty list to store individual dataframes
         list_of_dfs = []

         #Iterate through each worksheet
         for sheet in f.sheet_names:
            #parse data from each worksheet as a pandas dataframe
            df = f.parse(sheet)

            #And append it to the list 
            list_of_dfs.append(df)

         #combine all dataframes into one
         df = pd.concat(list_of_dfs, ignore_index=True)
         return render_template("excel.html",tables=[df.to_html(classes=['data','table-bordered', 'table-striped', 'table-hover', 'table-sm'])], titles=df.columns.values, uid = uid, fname = filename)

      elif filename.endswith('.xls'):
         # load excel file using pandas
         f = pd.ExcelFile(staging_directory+uid+"/"+filename)

         #define an empty list to store individual dataframes
         list_of_dfs = []

         #Iterate through each worksheet
         for sheet in f.sheet_names:
            #parse data from each worksheet as a pandas dataframe
            df = f.parse(sheet)

            #And append it to the list 
            list_of_dfs.append(df)

         #combine all dataframes into one
         df = pd.concat(list_of_dfs, ignore_index=True)

         return render_template("excel.html",tables=[df.to_html(classes=['data','table-bordered', 'table-striped', 'table-hover', 'table-sm'])], titles=df.columns.values, uid = uid, fname = filename)

      elif filename.endswith('.pdf'):
         lines = 0
         data = {}
         # read all the file contents and page number of an x pdf 
         pdfFileObj = open(staging_directory+uid+"/"+filename,"rb")
         # creating a pdf reader object
         try:
            pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
            
            #_files = []
            #_dict = {}
            # printing number of pages in pdf file
            print(pdfReader.numPages)
         
            for page in range(pdfReader.numPages):
               # creating a page object
               pageObj = pdfReader.getPage(page)
               # extracting text from page
               #print(pageObj.extractText())
            
               text = pageObj.extractText().split("\n")
               #_files.append(pageObj.extractText().split("\n"))
               #_dict[page] = pageObj.extractText().split("\n")
               
               for page in range(len(text)):
                  # Printing the line
                  # Lines are seprated using "\n"
                  print(text[page],end="\n")
                  data[lines] = text[page]
                  lines += 1
            # closing the pdf file object
            pdfFileObj.close()    
            return render_template("pdf.html",len = lines, content = data, uid = uid, fname = filename)
         except (PyPDF2.errors.PdfReadError,IndexError):
            path = staging_directory+uid+"/"+filename
            subprocess.Popen([path], shell=True)
            return Response("Unable to view data, "+ filename +" is opened",status=201,mimetype='application/json')

def get_files(output_dir):
   for file in os.listdir(output_dir):
      if os.path.isdir(os.path.join(output_dir, file)):
         return (os.listdir(output_dir))
      elif os.path.isfile(os.path.join(output_dir, file)):
         return (os.listdir(output_dir))

@app.route("/extract", methods=['POST','GET'])
def extract():
   try:
      output_dir = working_path+'output/'
      if request.method == "GET": 
         files=[]
         for file in get_files(output_dir):
            files.append(file)
            print(files)      
      return render_template('extract.html', files=get_files(output_dir))
   except (FileNotFoundError, IOError):
      response = "No files existing in the location, start uploading"
      return Response(response,status=201,mimetype='application/json')
       
if __name__ == "__main__":
   # Bind to PORT if defined, otherwise default to 5000.
   port = int(os.environ.get('PORT', 80))
   app.run(host='0.0.0.0', port=port, debug=True)
   

