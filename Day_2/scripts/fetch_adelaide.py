import string
import concurrent.futures
import progressbar
from itertools import chain
from urllib import request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup as bs

import json
import time

base = "https://ebooks.adelaide.edu.au"
def getLinks(letter):
    url = "/".join((base, "meta", "titles", letter))+".html"
    doc = request.urlopen(url).read()
    bsdata = bs(doc, "html.parser")
    return [''.join([base, res['href'],'complete.html'])
            for res in bsdata.find_all('ul', class_="works")[0].find_all('a')]

def retrievePage(wlink):
    try:
        doc = request.urlopen(wlink)
    except HTTPError as e:
        return
    return bs(doc.read(), "html.parser")

def processMetadata(page):
    if page is None:
        return {"description": "ERROR_COMP_NOT_FOUND"}
    bsworkjs = page.find('script', type='application/ld+json')
    if (bsworkjs):
        try:
            return json.loads(bsworkjs.get_text())
        except:
            return {"description": "ERROR_COMP_NOT_FOUND"}
    else:
        return {"description": "ERROR_COMP_NOT_FOUND"}

def processEbook(page):
    bsworkjs=page.find('script',type='application/ld+json')
    if (bsworkjs):
        return bsworkjs.prettify()
    else:
        return {"description": "ERROR_COMP_NOT_FOUND"}


#with concurrent.futures.ProcessPoolExecutor() as executor:
#    links = list(chain(*executor.map(getLinks, string.ascii_uppercase)))
for letter in string.ascii_uppercase[11:]:
    links = getLinks(letter)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        print('Submit futures :')
        bar = progressbar.ProgressBar()
        futures = []
        for link in bar(links):
            future = executor.submit(retrievePage, link)
            future.link = link
            futures.append(future)

        print('Retrieve pages {}'.format(letter))
        bar = progressbar.ProgressBar(max_value=len(futures))
        pages = []
        for future in bar(concurrent.futures.as_completed(futures)):
            try:
                pages.append((future.link, str(future.result())))
            except:
                pages.append((future.link, None))
    
        #print('Submit futures: ')
        #bar = progressbar.ProgressBar()
        #futures = [executor.submit(processMetadata, page) for page in bar(pages)]
        #print('Retrieve metadata {}'.format(letter))
        #bar = progressbar.ProgressBar(max_value=len(futures))
        #meta = [future.result() for future in bar(concurrent.futures.as_completed(futures))]
    
    with open('adelaide_page_{}.json'.format(letter), 'w') as file_:
        file_.writelines("\n".join(json.dumps(page_i) for page_i in pages))
#    with open('adelaide_meta_{}.json'.format(letter), 'w') as file_:
#        file_.writelines("\n".join(json.dumps(meta_i) for meta_i in meta))
