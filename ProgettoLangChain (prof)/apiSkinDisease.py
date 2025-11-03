import requests

url = "https://detect-skin-disease1.p.rapidapi.com/skin-disease"

payload = {}
headers = {
	"x-rapidapi-key": "653b32e85fmsh8c6fdd614fd109bp15c804jsn8b3353fa29f0",
	"x-rapidapi-host": "detect-skin-disease1.p.rapidapi.com",
	"Content-Type": "application/x-www-form-urlencoded"
}

response = requests.post(url, data=payload, headers=headers)

result = print(response.json())

