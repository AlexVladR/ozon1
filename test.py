import os
import time
import pytest
import requests

url_r = 'https://cloud-api.yandex.net/v1/disk/resources'
xtoken=os.environ['token']
attempt_numb=max(1,int(os.environ['attempt_numb']))
headers = {'Content-Type': 'application/json', 'Accept': 'application/json', 'Authorization': f'OAuth {xtoken}'}
folder='test_folder'

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
        try:
            xparams = {"path": path}
            res=requests.get(f'{url_r}',params=xparams,headers = headers)
            return checkResponse(res)
        except Exception as err:
            return {
                    'isSuccess': False,
                    'error': str(err)
            }
    def delete_folder(self, path):
        xparams={"path":path,"permanently":False} #,"force_async":True}
        try:
            res=requests.delete(f'{url_r}', params=xparams,headers = headers)
            return checkResponse(res)
        except Exception as err:
            return {
                    'isSuccess': False,
                    'error': str(err)
            }
    def lazy_delete_folder(self, path):
        x=path
        res1=self.check_folder(path)
        if not 'statusCode'in res1:
           return {'isSuccess': False, 'error': f"Error. lazy_delete_folder\ncheck_folder\n{str(res1['error'])}\n"}
        while res1['statusCode'] < 300:
            res=self.delete_folder(path)
            if not 'statusCode' in res:
                return {'isSuccess': False, 'error': f"Error. lazy_delete_folder\ndelete_folder\n{str(res['error'])}\n"}
            res1 = self.check_folder(path)
        return {'isSuccess': True}

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
    def __init__(self):
        pass
    url_dogs = "https://dog.ceo/api/breeds"
    url_dog = "https://dog.ceo/api/breed"
    point="images/random"
    allBreeds = list(requests.get(f'{url_dogs}/list/all').json()["message"].keys())
    def get_sub_breeds(self,breed):
        try:
            res = requests.get(f'{self.url_dog}/{breed}/list')
            return checkResponse(res)
        except Exception as err:
            return {'isSuccess': False, 'error': str(err)}
    def get_urls(self,breed, sub_breeds):
        xstr=""
        url_images = []
        if sub_breeds:
            for sub_breed in sub_breeds:
                try:
                    res1 = requests.get(f"{self.url_dog}/{breed}/{sub_breed}/{self.point}")
                    sub_breed_urls = res1.json().get('message')
                    url_images.append(sub_breed_urls)
                except Exception as err:
                    xstr += f"Error.\n{self.url_dog}/{breed}/{sub_breed}/{self.point}.\nКод ={res1.get('statusCode')}.\n{str(err)}."
        else:
            try:
                res1=requests.get(f"{self.url_dog}/{breed}/{self.point}")
                url_images.append(res1.json().get('message'))
            except Exception as err:
                xstr += f"Error.\n{self.url_dog}/{breed}/{self.point}.\nКод ={res1.get('statusCode')}.\n{str(err)}."

        if xstr=="":
           return {'isSuccess': True, 'list':url_images,'error': ""}
        else:
            return {'isSuccess': False, 'list': "", 'error': xstr}

yandex_client = YaUploader()
dog=Dog()
def u(breed,errors):
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
                         for index,value in enumerate(urls,start=1):
                            part_name = value.split('/')
                            name = f"{part_name[-2]}_{str(index)}_{os.path.splitext(value)[1]}"
                            res4=yandex_client.upload_photos_to_yd(folder, value, name)
                            if not res4['isSuccess']:
                              errors.append(res4['error'])
                              break
                  else:
                      errors.append(f"Для породы {breed} не найдено ни одного изображения.")
              else:
                  errors.append(f"Error.\nФормирование списка изображений. Порода {breed}.\nКод ={str(res2.get('statusCode'))}.\n{str(res2['error'])}.")
          else:
              errors.append(f"Error.\nget_sub_breeds. Порода {breed}.\nКод ={str(res1.get('statusCode'))}.\n{str(res1['error'])}.")
      else:
          errors.append(res['error'])

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

def check_items(breed,get_sub_breeds,response,errors):
    if len(get_sub_breeds) == 0:
        try:
           assert len(response['json']['_embedded']['items']) == 1
        except AssertionError:
           errors.append(f"Некорректное количество items.\nОР: 1\nФР: {len(response['json']['_embedded']['items'])}\n")
    else:
        try:
            assert len(response['json']['_embedded']['items']) == len(get_sub_breeds)
        except AssertionError:
            errors.append(f"Некорректное количество items.\nОР: 1\nФР: {len(response['json']['_embedded']['items'])}\n")
    for item in response['json']['_embedded']['items']:
        try:
            assert item['type'] == 'file'
        except AssertionError:
            errors.append(f"Некорректный тип item[{response['json']['_embedded']['items'].index(item)}].\nОР: file\nФР: {item['type']}\n")
        try:
            assert item['name'].startswith(breed)
        except AssertionError:
            errors.append(f"Некорректный name item[{response['json']['_embedded']['items'].index(item)}].\nОР: name начинается с {breed}\nФР: name={item['name']}\n")

class TestAPI:
    errors = []
    @pytest.mark.parametrize('breed', dog.allBreeds)
    def test_proverka_upload_dog(self,breed):
        self.errors=[]
        # подготовка тестовых данных
        u(breed,self.errors)
        if not self.errors:
            # проверка
            xparams = {
                       "path": folder,
                       "limit":100
                      }
            response = yandex_client.get_resources(xparams)
            if response['isSuccess']:
                assert response['json']['type'] == "dir",f"Некорректный тип.\nОР: dir\nФР: {response['json']['type']}\n"
                assert response['json']['name'] == folder,f"Некорректный name папки.\nОР: {folder}\nФР: {response['json']['name']}\n"
                res1=dog.get_sub_breeds(breed)
                if res1['isSuccess']:
                    check_items(breed,res1['json']['message'],response,self.errors)
                else:
                    self.errors.append(f"Ошибка получения данных породы {breed}\nПараметры:{str(xparams)}.\n{str(res1['error'])}\n")
            else:
                self.errors.append(f"Ошибка получения данных ресурса\nПараметры:{str(xparams)}.\n{str(response['error'])}\n")
        # удаление тестовых данных
        res = yandex_client.lazy_delete_folder(folder)
        if not res['isSuccess']:
           self.errors.append(f"Ошибка ленивого удаления тестовых данных породы {breed}\n{str(res['error'])}\n")
        if self.errors:
            pytest.fail("\n" + "\n".join(self.errors))
