#importing packages
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from sqlalchemy import create_engine
import os

def get_page(url):
    r = requests.get(url)

    if r.status_code == 200:
        return BeautifulSoup(r.text,'html.parser')
    else: 
        print(f"something went wrong. status code: {r.status_code}")
    
def get_agreement(block):
    # grabs the agreement id, start date and end date
    for i in block.find_all('li'):
        if i.find('strong').text.strip() == 'Agreement ID:':
            agreement_id = i.text.split(':')[-1].strip()
        elif i.find('strong').text.strip() == 'Start Date:':
            start_date = i.text.split(':')[-1].strip()
        elif i.find('strong').text.strip() == 'End Date:':
            end_date = i.text.split(':')[-1].strip()
        else:
            agreement_id = start_date = end_date = "Not available"
    return agreement_id, start_date, end_date


username = os.environ.get("DB_USER")
password = os.environ.get("DB_PASS")
host = os.environ.get("DB_HOST")
port = os.environ.get("DB_HOST")
database = os.environ.get("DB_NAME")

if __name__ == "__main__":
    list_of_info = []
    DELAY = 10
    for i in range(1,7):
        url = f"https://www.crowncommercial.gov.uk/agreements/search/{i}?statuses%5B0%5D=live"
        tomato_soup = get_page(url)
        ul = tomato_soup.find('ul', class_='govuk-list govuk-list--frameworks')
        blocks = ul.find_all('li')
        for block in blocks:
            #skips if cant find the 'a' tag
            if block.find('a') is None:
                continue
            
            name = block.find('a').text.strip()
            agreement_id, start_date,end_date = get_agreement(block)
            short_description = block.find('p').text.strip()
            
            # get the link for the second page
            url2 = block.find('a').get('href')
            carrot_soup = get_page("https://www.crowncommercial.gov.uk/"+ url2)
            description_header = carrot_soup.find_all('div',class_="govuk-accordion__section")
            for i in description_header:
                title = i.find('div',class_="govuk-accordion__section-header")
                if title.text.strip() == "Description":
                    long_description = i.find("div", class_="wysiwyg-content").text.strip()

            
            dict_of_info = {
                "agreement_id": agreement_id,
                "agreement_name": name,
                "start_date": start_date,
                "end_date": end_date,
                "short_description": short_description,
                "long_description": long_description,
            }
            list_of_info.append(dict_of_info)
            time.sleep(DELAY)
            print(f"{agreement_id}, {name}, {start_date},{end_date}")
        
    df = pd.DataFrame(list_of_info)
    print(df.head(10))
    # save to csv file
    df.to_csv('CrownCommercial.csv', index=False)


    # Create the database connection URL
    engine = create_engine(f'postgresql://{username}:{password}@{host}:{port}/{database}')

    df.to_sql('crowncommercial', con=engine, if_exists='append', index=False)