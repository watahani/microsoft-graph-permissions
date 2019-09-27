import requests
import re
from bs4 import BeautifulSoup

source_uri_v1 = "https://docs.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0" 

r = requests.get(source_uri_v1)

soup = BeautifulSoup(r.content, 'html.parser')

elms = soup.find_all(href=re.compile("microsoft"))

print(elms)
