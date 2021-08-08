from flask import Flask
from flask import request
from urllib.parse import unquote
import json
import logging

from azure.core.exceptions import (ResourceExistsError, ResourceNotFoundError)
from azure.storage.fileshare import (ShareServiceClient,ShareClient,ShareDirectoryClient,ShareFileClient)
import os
from github import Github

app = Flask(__name__)

@app.route('/hello/', methods=['GET', 'POST'])

 
def hello():

    print('######## fetch and process payload data ########')
    added_files, removed_files, modified_files, files = [],[],[],[]

    if request.get_data():
        payload_data = request.get_data()
        #print(f' payload data print: {payload_data}')
        dict_data = json.loads(payload_data)
        #print(f'Dictionary Data Print : {dict_data}')

        aa = type(dict_data)
        print(f'type of new data: {aa}')
        print(f'######## extracting filenames from payload ########')
       
        for i,j in dict_data.items():
            if i == 'ref':
                reference_id = j
                print("reference id is::",j)

            if i == 'commits':
                print("inside commits")
                for valuess in j:
                    for key,value in valuess.items():
                        if key == 'added':
                            print("inside added")
                            if value:    
                                for key_values in value:
                                    added_files.append(key_values)
                            
                        elif key == 'removed':
                            print("inside removed")

                            if value:
                                for key_values in value:
                                    removed_files.append(key_values)

                        elif key == 'modified':
                            print("inside modified")

                            if value:
                                for key_values in value:
                                    modified_files.append(key_values)                                                                                                            

        print('addded::',added_files)
        print('removed::',removed_files)
        print('modified::',modified_files)

    else:
        print(f"Havent recevied any payload")


    try:
        files_list = []
        if len(added_files) != 0 :
            files_list.append(added_files)

        elif len(modified_files) != 0:
            files_list.append(modified_files)

        elif len(removed_files) != 0:
            #NO need to download this, hence not appending to list
            print(f'skip the remove file append to list')     

 

        ## Let us check the files names to download     
        print(f'list the file names to download \n')

        if files_list:
            for file_name in files_list:
                print(f'Name of file to download : {file_name}')
        else:
            ## For testing purpose hardcoding the modified file
            files_list = ['testing']
            reference_id = "refs/heads/master" 
            for file_name in files_list:
                print(f'Hardcoded list : {file_name}')
 

    except Exception as err:
        print("Downloaded file parsing error:: {err}")
        return "failed while appending files"

 

    ###### Code logic for Github connection
    try:
        print(f'######### downloading file #######')
        g = Github(login_or_token='37650bc7186988e7e3864877b846d0ed9ec8575b', base_url='https://github.comcast.com/api/v3')
        user = g.get_user()
        print(f'username: {user}')
        login = user.login
        print(f' UserName: ',login)
        repo = g.get_repo("XMDET/DeviceAutomation")
        print(repo,'***')

    except Exception as err:
        print('Git login error:')
        return "failed login to git"                        

    try:
        ## Now time to download each file
        for file_name in files_list:
            contents = repo.get_contents(file_name,ref=reference_id)

            #### download files raw data
            data = contents.decoded_content
            new_data = data.decode('utf-8')
            print(new_data)
            a = new_data
            print(f'file content {a}')

            with open(file_name,'w') as file:
                file.write(a)

            print(f'created local file::',file_name)

                                                  
        ####### Uploading files to Azure
        try:
            connection_string = "DefaultEndpointsProtocol=https;AccountName=strgact10;AccountKey=g6hKJsqM9MGo9eJZ3On7ZCOC11wszdAQLWHHaoCp8A5qwfJDdSvpjZweZDN3No9NKMRNDCx/mXWKMuRYRU9GfA==;EndpointSuffix=core.windows.net"
            share_name = "frameworkfinal"
            dest_file_folder = "testscripts/"
            for file_name in files_list:
                dest_file_name = file_name
                dest_file_path = dest_file_folder + dest_file_name
                service_client = ShareServiceClient.from_connection_string(connection_string)
                print(service_client)
                source_file = open(file_name, "rb")
                data = source_file.read()
                print(data)
                file_client = ShareFileClient.from_connection_string(connection_string, share_name, dest_file_path)
                print(file_client)
                print("Uploading to:", dest_file_path)
                file_client.upload_file(data)

        except:
            print(f'Azure function Error:')
            return "failed while uploading file"

    except Exception as err:
        print('Git file downloading Error:')
        return "failed while downloading from git"

    return "Success"

 

if __name__=='__main__':
    app.run(host='0.0.0.0', port=8000)
