import requests

url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
params = {
    "app_id": "c11c4ab2",
    "app_key": "c7e6f1ee6ff902480322a5d459010689",
    "results_per_page": 10,
    "what": "developer",       # search keyword
    "where": "India",          # location
    "content-type": "application/json"
}

response = requests.get(url, params=params)
data = response.json()

list = []
for job in data['results']:
    list.append({
        "title": job['title'],
        "company": job['company']['display_name'],
        "location": job['location']['display_name'],
        "description": job['description'],
        "date": job['created'],
        "link": job['redirect_url']
    })
