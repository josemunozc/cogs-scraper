import sys
import requests
import getpass
import re
import pandas as pd
from bs4 import BeautifulSoup

def get_id_value(id_name,soup):
  matches=soup.find_all(id=id_name)
  assert len(matches)==1, f"number equal to 1 expected, got: {len(matches)}"
  return matches[0].get('value')


def get_project_number(soup):
  project_number="NAN"
  matches=soup.find_all("div", {"class": "breadcrumbs"})
  assert len(matches)==1, f"number equal to 1 expected, got: {len(matches)}"
  match=re.search('scw....',matches[0].text)
  if match:
    project_number=match.group()

  return project_number


def get_number_of_pages(scw_uni='cardiff'):
  # get number of pages with cardiff projects
  # ['1', '2', '3', '4', '5', '6', '7', '634', 'Projects']
  addr = "https://scw.bangor.ac.uk/en-gb/admin/project/project/?p=0&q="+scw_uni
  r = client.get(addr)
  soup = BeautifulSoup(r.text, 'html.parser')
  matches=soup.find_all("p", class_='paginator')
  
  assert len(matches)==1, f"Only 1 'paginator' match expected, got: {len(matches)}"
  paginator_list=matches[0].text.split()

  assert paginator_list[-1:][0]=="Projects", f"Last item expected to be 'Projects', got {paginator_list[-1:][0]}"
  assert int(paginator_list[-2:][0])>600, f"second to last item expected to be higher than 600, got {paginator_list[-2:][0]}"

  pages=[int(i) for i in paginator_list[:-2]]
  return(pages[-1:][0])


URL = 'https://scw.bangor.ac.uk/en-gb/admin/login/?next=/en-gb/admin/'
client = requests.session()

# Retrieve the CSRF token first
client.get(URL)  # sets cookie
print(client.cookies)
if 'csrftoken' in client.cookies:
    # Django 1.6 and up
    csrftoken = client.cookies['csrftoken']
else:
    # older versions
    csrftoken = client.cookies['csrf']


EMAIL=input("Username: ")
PASSWORD=getpass.getpass()

login_data = dict(username=EMAIL, password=PASSWORD, csrfmiddlewaretoken=csrftoken, next='/en-gb/admin/')
r = client.post(URL, data=login_data, headers=dict(Referer=URL))


#################################################
# Create list of Cardiff projects and web codes #
#################################################
cardiff_projects=[]
cardiff_projects_web_codes=[]
for page in range(0,get_number_of_pages()):
    addr="https://scw.bangor.ac.uk/en-gb/admin/project/project/?p="+str(page)+"&q=cardiff"
    print(addr)
    # build list of cardiff projects
    r = client.get(addr)
    soup = BeautifulSoup(r.text, 'html.parser')
    matches=soup.find_all(href=re.compile("project/\d+"))

    for match in matches:
      cardiff_projects.append(match.text)
      project_web_code=re.findall(r'/\d+/',match['href'])
      project_web_code=re.findall(r'\d+',project_web_code[0])
      cardiff_projects_web_codes.append(project_web_code[0])


#print(cardiff_projects)
#print(cardiff_projects_web_codes)

#################################################
# Get PI information                            #
#################################################
rows=[]
for project in cardiff_projects_web_codes:
  addr='https://scw.bangor.ac.uk/en-gb/admin/project/project/'+project+'/change/'
  r = client.get(addr)
  soup = BeautifulSoup(r.text, 'html.parser')
  #print(soup.prettify())

  project_number=get_project_number(soup) 
  # now get PI information, problem is that some fields might be empty 
  pi_name=get_id_value('id_pi_name',soup)
  pi_position=get_id_value('id_pi_position',soup)
  pi_email=get_id_value('id_pi_email',soup)

  if pi_name is None:
    pi_name="NAN"

  if pi_email is None:
    pi_email="NAN"

  if pi_position is None:
    pi_position="NAN"

  print("Project....: " + project_number)
  print("PI Name....: " + pi_name)
  print("PI position: " + pi_position)
  print("PI email...: " + pi_email)

  rows.append([project_number,pi_name,pi_position,pi_email])
  print('---')


df = pd.DataFrame(rows, columns=["Project number","PI name","PI position","PI email"])
df.to_csv("results.txt")
