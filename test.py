import os
import random
import time
import pytest
import requests

url_r = 'https://cloud-api.yandex.net/v1/disk/resources'
xtoken=os.environ['token']
attempt_numb=max(1,int(os.environ['attempt_numb']))
url_dog="https://dog.ceo/api/breed"
headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {xtoken}'}
folder='test_folder'
allBreeds=list(requests.get(f'https://dog.ceo/api/breeds/list/all').json()["message"].keys())
class YaUploader:
    def __init__(self):
        pass

    def get_resources(self,params):
        try:
            res = requests.get(f'{url_r}',params=params, headers=headers)
            return checkResponse(res)
        except Exception as err:
            return {
                'isSuccess': False,
                'error': str(err)
            }

    def create_folder(self, path):
        try:
            res = requests.put(f'{url_r}?path={path}', headers=headers)
            return checkResponse(res)
        except Exception as err:
            return {
                'isSuccess': False,
                'error': str(err)
            }

    def check_folder(self, path):
        res=None
        try:
            res=requests.get(f'{url_r}?path={path}', headers = headers)
            x1=checkResponse(res)
            return checkResponse(res)
        except Exception as err:
            return {
                    'isSuccess': False,
                    'error': str(err)
            }
    def delete_folder(self, path):
        res=None
        xparams={"path":path,"permanently":True} #,"force_async":True}
        try:
            res=requests.delete(f'{url_r}', params=xparams,headers = headers)
            x2 = checkResponse(res)
            return checkResponse(res)
        except Exception as err:
            return {
                    'isSuccess': False,
                    'error': str(err)
            }
    def lazy_delete_folder(self, path):
        res=self.check_folder(path)
        while res.get('statusCode')<300:
            self.delete_folder(path)
            time.sleep(1)
            res = self.check_folder(path)
        return {'isSuccess': True, 'text': f"Ресурс {path} удален"}
    def upload_photos_to_yd(self, path, url_file, name):
        xres = {'isSuccess': False}
        url = f"{url_r}/upload"
        params = {"path": f'{path}/{name}', 'url': url_file}
        for i in range(attempt_numb):
            xres = {'isSuccess': True}
            resp = requests.post(url, headers=headers, params=params)
            if resp.status_code<300:
                url_oper=resp.json()["href"]
                res = requests.get(f'{url_oper}', headers=headers).json()
                time.sleep(1)
                while res["status"]!='success':
                    if res["status"] == 'failed':
                        xres={'isSuccess': False,
                              'statusCode': "None",
                              'error': f"Error. upload_photos_to_yd\nСтатус асинхронной операции=failed\nurl={url}\nparams={str(params)}"
                        }
                        break
                    time.sleep(3)
                    res = requests.get(f'{url_oper}', headers=headers).json()
            else:
               xres= {
                       'isSuccess': False,
                       'statusCode': resp.status_code,
                       'error': f"Error. uploadupload_photos_to_yd\nКод={resp.status_code} {str(resp.json()['message'])}"
               }
            if xres['isSuccess']:
                break
        return xres
class Dog:
    def get_sub_breeds(self,breed):
        try:
            res = requests.get(f'{url_dog}/{breed}/list')
            return checkResponse(res)
        except Exception as err:
            return {'isSuccess': False, 'error': str(err)}
    def get_urls(self,breed, sub_breeds):
        xstr=""
        url_images = []
        if sub_breeds:
            for sub_breed in sub_breeds:
                try:
                    res1 = requests.get(f"{url_dog}/{breed}/{sub_breed}/images/random")
                    sub_breed_urls = res1.json().get('message')
                    url_images.append(sub_breed_urls)
                except Exception as err:
                    xstr += f"Error.\n{url_dog}/{breed}/{sub_breed}/images/random.\nКод ={res1.get('statusCode')}.\n{str(err)}."
        else:
            try:
                res1=requests.get(f"{url_dog}/{breed}/images/random")
                url_images.append(res1.json().get('message'))
            except Exception as err:
                xstr += f"Error.\n{url_dog}/{breed}/images/random.\nКод ={res1.get('statusCode')}.\n{str(err)}."

        if xstr=="":
           return {'isSuccess': True, 'list':url_images,'error': ""}
        else:
            return {'isSuccess': False, 'list': "", 'error': xstr}

yandex_client = YaUploader()
dog=Dog()

def u(breed):
      xstr1=""
      res=yandex_client.lazy_delete_folder(folder)
      if res['isSuccess']:
          res1=dog.get_sub_breeds(breed)
          if res1['isSuccess']:
              sub_breeds = res1["json"]["message"]
              res2=dog.get_urls(breed, sub_breeds)
              if res2['isSuccess']:
                  urls=res2["list"]
                  if len(urls)>0:
                      res3=yandex_client.create_folder(folder)
                      if res3['isSuccess']:
                         for url in urls:
                            part_name = url.split('/')
                            name = '_'.join([part_name[-2], part_name[-1]])
                            res4=yandex_client.upload_photos_to_yd(folder, url, name)
                            if not res4['isSuccess']:
                              xstr=res4['error']
                              break
                  else:
                      xstr1+=f"Error.\nДля породы {breed} не найдено ни одного изображения."
              else:
                  xstr1+=f"Error.\nФормирование списка изображений. Порода {breed}.\nКод ={res.get('statusCode')}.\n{str(res['error'])}."
          else:
              xstr1 += f"Error.\nget_sub_breeds. Порода {breed}.\nКод ={res.get('statusCode')}.\n{str(res['error'])}."
      else:
          xstr1+=str(res['error'])
      return xstr1
def checkResponse(response):
    result = {}
    result["isSuccess"] = response.ok
    result["statusCode"] = response.status_code
    if response.ok:
        if "content-type" in response.headers:
            if "application/json" in response.headers["content-type"]:
                result["json"] = response.json()
            elif "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in response.headers["content-type"]:
                result["bytes"] = response.content
        if response.text != '' and not any(k in result for k in ("json", "text", "bytes")):
            result["text"] = response.content.decode()
    else:
        if "content-type" in response.headers:
            if "application/json" in response.headers["content-type"]:
                result["error"] = response.json()
        if response.text != '' and "error" not in result:
            result["error"] = response.content.decode()
        elif response.reason != '' and "error" not in result:
            result["error"] = response.reason
    return result

class TestAPI():
    @pytest.mark.parametrize('breed', ['doberman', random.choice(['bulldog', 'collie'])])
    #@pytest.mark.parametrize('breed', allBreeds)
    def test_proverka_upload_dog(self,breed):
        xstr=""
        res=u(breed)
        if not res=="":
            xstr+=f'{res}\n'
        else:
            # проверка
            xparams = {
                       "path": folder,
                       "limit":100
                      }
            response = yandex_client.get_resources(xparams)
            if response['isSuccess']:
                if response['json']['type'] != "dir":
                    xstr+=f"Некорректный тип.\nОР: dir\nФР: {response.json()['type']}\n"
                if response['json']['name'] != folder:
                    xstr += f"Некорректный name папки.\nОР: {folder}\nФР: {response.json()['name']}\n"
                res1=dog.get_sub_breeds(breed)
                if res1['isSuccess']:
                    xget_sb=res1['json']['message']
                    if xget_sb == []:
                        if len(response['json']['_embedded']['items']) != 1:
                            xstr += f"Некорректное количество items.\nОР: 1\nФР: {len(response['json']['_embedded']['items'])}\n"
                        for item in response['json']['_embedded']['items']:
                            if item['type'] != 'file':
                               xstr += f"Некорректный тип item[{response['json']['_embedded']['items'].index(item)}].\nОР: file\nФР: {item['type']}\n"
                            if not item['name'].startswith(breed):
                                xstr += f"Некорректный name item[{response['json']['_embedded']['items'].index(item)}].\nОР: name начинается с {breed}\nФР: name={item['name']}\n"

                    else:
                        if len(response['json']['_embedded']['items']) != len(xget_sb):
                            xstr += f"Некорректное количество items.\nОР: {len(xget_sb)}\nФР: {len(response['json']['_embedded']['items'])}\n"
                        for item in response['json']['_embedded']['items']:
                            if item['type'] != 'file':
                               xstr += f"Некорректный тип item[{response['json']['_embedded']['items'].index(item)}].\nОР: file\nФР: {item['type']}\n"
                            if not item['name'].startswith(breed):
                                xstr += f"Некорректный name item[{response['json']['_embedded']['items'].index(item)}].\nОР: name начинается с {breed}\nФР: name={item['name']}\n"
                else:
                    xstr += f"Ошибка получения данных породы {breed}\nПараметры:{str(xparams)}.\n{str(response['err'])}\n"
            else:
                xstr+= f"Ошибка получения данных ресурса\nПараметры:{str(xparams)}.\n{str(response['err'])}\n"

        yandex_client.lazy_delete_folder(folder)

        assert xstr=="", xstr