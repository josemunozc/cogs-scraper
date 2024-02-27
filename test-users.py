import sys
import requests
import getpass
import re
import pandas as pd
import bs4
from bs4 import BeautifulSoup

def get_user_account_status(soup):
  matches=soup.find_all('select',id="id_shibbolethprofile-0-account_status")
  if len(matches) == 0:
      matches=soup.find_all('select',id="id_profile-0-account_status")

  assert len(matches)>0, f"No matches found in account status."

  for child in matches[0].children:
      if isinstance(child,bs4.element.Tag):
              if child.has_attr('selected'):
                      user_account_status=child.contents[0]

  return user_account_status


def get_user_details(soup):
  user_name="NAN"
  user_account="NAN"
  matches=soup.find_all("div", {"class": "breadcrumbs"})
  assert len(matches)==1, f"number equal to 1 expected, got: {len(matches)}"
  match=re.search('.*@cardiff.ac.uk.*',matches[0].text)
  #print(match.group())
  if match:
    m=re.search('› (.*) \((.*)@cardiff.ac.uk.*\)',match.group())
    user_name=m.group(1)
    user_account=m.group(2)
    #print(user_name)
    #print(user_account)
  return user_name,user_account


def get_number_of_pages(scw_uni='cardiff'):
  # get number of pages with cardiff projects
  # ['1', '2', '3', '4', '5', '6', '7', '634', 'Projects']
  addr = "https://scw.bangor.ac.uk/en-gb/admin/users/customuser/?q="+scw_uni
  r = client.get(addr)
  soup = BeautifulSoup(r.text, 'html.parser')
  matches=soup.find_all("p", class_='paginator')
  assert len(matches)==1, f"Only 1 'paginator' match expected, got: {len(matches)}"
  paginator_list=matches[0].text.split()
  assert paginator_list[-1:][0]=="Users", f"Last item expected to be 'Users', got {paginator_list[-1:][0]}"
  assert int(paginator_list[-2:][0])>600, f"second to last item expected to be higher than 600, got {paginator_list[-2:][0]}"
  return(int(paginator_list[-3]))


# Start main program
URL = 'https://scw.bangor.ac.uk/en-gb/admin/login/?next=/en-gb/admin/'
client = requests.session()

# Retrieve the CSRF token first
client.get(URL)  # sets cookie
#print(client.cookies)
if 'csrftoken' in client.cookies:
    # Django 1.6 and up
    csrftoken = client.cookies['csrftoken']
else:
    # older versions
    csrftoken = client.cookies['csrf']


#EMAIL=input("Username: ")
#PASSWORD=getpass.getpass()
EMAIL="c1045890@cardiff.ac.uk"
PASSWORD="B21&*iXiicvCIw8ke9^"

login_data = dict(username=EMAIL, password=PASSWORD, csrfmiddlewaretoken=csrftoken, next='/en-gb/admin/')
r = client.post(URL, data=login_data, headers=dict(Referer=URL))


#################################################
# Create list of Cardiff users and web codes #
#################################################
cardiff_users=[]
cardiff_users_web_codes=[]
#for page in range(1,2):
#for page in range(1,get_number_of_pages()+1):
number_of_pages=get_number_of_pages()
for page in range(number_of_pages,number_of_pages+1):
    addr="https://scw.bangor.ac.uk/en-gb/admin/users/customuser/?p="+str(page)+"&q=cardiff"
    #print(addr)
    # build list of cardiff users
    r = client.get(addr)
    soup = BeautifulSoup(r.text, 'html.parser')
    matches=soup.find_all(href=re.compile("customuser/\d+"))
    #print(matches)
    for match in matches:
      cardiff_users.append(match.text)
      user_web_code=re.findall(r'/\d+/',match['href'])
      user_web_code=re.findall(r'\d+',user_web_code[0])
      cardiff_users_web_codes.append(user_web_code[0])


#################################################
# Get user information                            #
#################################################
rows=[]
#for user in cardiff_users_web_codes:
for user in cardiff_users_web_codes:
  addr='https://scw.bangor.ac.uk/en-gb/admin/users/customuser/'+user+'/change/'
  r = client.get(addr)
  soup = BeautifulSoup(r.text, 'html.parser')
  #print(soup.prettify())

  user_name,user_account=get_user_details(soup) 
  user_account_status=get_user_account_status(soup)
  print(f"{user_account},{user_name},{user_account_status}")


