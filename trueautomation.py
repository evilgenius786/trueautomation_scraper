import csv
import json
import os.path
import time
import traceback

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

url = 'https://bexar.trueautomation.com/clientdb/?cid=110'
t = 1
timeout = 3
inputfile = 'input.csv'
errorfile = 'error.csv'
outputfile = 'output.csv'
nodatafile = 'nodata.csv'
csvheader = ["First Name", "Last Name", "Mailing Address", "Mailing City", "Mailing State", "Mailing Zip Code",
             "Property Address", "Property City", "Property State", "Property Zip Code"]
debug = False

headless = False
images = False
max = False

incognito = True


def scrape(driver, addr):
    global t
    print("Working on", addr)
    driver.get(url)
    sendkeys(driver, '//*[@id="propertySearchOptions_searchText"]', addr + "\n")
    trs = getElements(driver, '//*[@id="propertySearchResults_resultsTable"]/tbody/tr')[1:-1]
    if len(trs) < 1:
        append(nodatafile, [addr], False)
        print("No data found for", addr)
        return
    for tr in trs:
        href = getElement(tr, './td[10]/a').get_attribute('href')
        try:
            print('Getting data of row', tr.text, href)
            soup = BeautifulSoup(requests.get(href).content, 'lxml')
            name = get(soup, 'Name').split(' ')
            paddr = get(soup, 'Address').split('  ')
            maddr = get(soup, 'Mailing Address').split('  ')
            fname = name[0]
            lname = name[-1] if len(name[-1]) > 3 else name[1]
            name = name[1:]
            name.reverse()
            for n in name:
                if len(n) > 3:
                    lname = n
                    break
            row = [lname,
                   fname,
                   maddr[-2],
                   maddr[-1].split(', ')[0],
                   maddr[-1].split(', ')[1].split(' ')[0],
                   maddr[-1].split(', ')[1].split(' ')[1],
                   paddr[-2],
                   paddr[-1].split(', ')[0],
                   paddr[-1].split(', ')[1].split(' ')[0],
                   paddr[-1].split(', ')[1].split(' ')[1]
                   ]
            data = {'First name': row[0],
                    'Last name': row[1],
                    'Mailing Address': row[2],
                    'Mailing City': row[3],
                    'Mailing State': row[4],
                    'Mailing ZIP Code': row[5],
                    'Property Address': row[6],
                    'Property City': row[7],
                    'Property State': row[8],
                    'Property ZIP Code': row[9]
                    }
            print(json.dumps(data, indent=4))
            append(outputfile, row)

        except:
            print('Error on address', addr)
            traceback.print_exc()
            append(errorfile, [addr], False)
    time.sleep(t)


def append(file, row, read=True):
    if read:
        with open(file, 'r', newline='', errors='ignore', encoding='utf8') as outfile:
            for r in csv.reader(outfile):
                if row == r:
                    print("Already scraped!")
                    return
    with open(file, 'a+', newline='', errors='ignore', encoding='utf8') as outfile:
        csv.writer(outfile).writerow(row)


def get(soup, text, tries=3):
    if tries == 0:
        return "Error"
    try:
        return soup.find('td', string=f"{text}:").findNext('td').text.strip()
    except:
        print("Request blocked! trying again.")
        time.sleep(1)
        return get(soup, text, tries - 1)


def main():
    os.system('color 0a')
    logo()
    rows = []
    global t
    if not os.path.isfile(outputfile):
        append(outputfile, csvheader, False)
    if not os.path.isfile(inputfile):
        append(inputfile, csvheader, False)
        print("Please enter data in", inputfile)
        return
    with open(inputfile, 'r', newline='', errors='ignore', encoding='utf8') as outfile:
        for r in csv.reader(outfile):
            rows.append(r)
    start = input("Enter Starting Row (1): ")
    start = 1 if (start == "" or int(start) < 1) else int(start)
    end = input("Enter Ending Row (Last row): ")
    end = len(rows) if (end == "" or int(end) > len(rows)) else int(end)
    t = input("Enter Time (1-4) for Delay (1): ")
    t = 1 if t == "" else int(t)
    driver = getChromeDriver()
    for i in range(start, end):
        addr = rows[i][6].strip()
        scrape(driver, " ".join(addr.split()))
        time.sleep(t)


def click(driver, xpath, js=False):
    if js:
        driver.execute_script("arguments[0].click();", getElement(driver, xpath))
    else:
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath))).click()


def getElement(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))


def getElements(driver, xpath):
    return WebDriverWait(driver, timeout).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))


def sendkeys(driver, xpath, keys, js=False):
    if js:
        driver.execute_script(f"arguments[0].value='{keys}';", getElement(driver, xpath))
    else:
        getElement(driver, xpath).send_keys(keys)


def getChromeDriver(proxy=None):
    options = webdriver.ChromeOptions()
    if debug:
        # print("Connecting existing Chrome for debugging...")
        options.debugger_address = "127.0.0.1:9222"
    else:
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
    if not images:
        # print("Turning off images to save bandwidth")
        options.add_argument("--blink-settings=imagesEnabled=false")
    if headless:
        # print("Going headless")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    if max:
        # print("Maximizing Chrome ")
        options.add_argument("--start-maximized")
    if proxy:
        # print(f"Adding proxy: {proxy}")
        options.add_argument(f"--proxy-server={proxy}")
    if incognito:
        # print("Going incognito")
        options.add_argument("--incognito")
    return webdriver.Chrome(options=options)


def getFirefoxDriver():
    options = webdriver.FirefoxOptions()
    if not images:
        # print("Turning off images to save bandwidth")
        options.set_preference("permissions.default.image", 2)
    if incognito:
        # print("Enabling incognito mode")
        options.set_preference("browser.privatebrowsing.autostart", True)
    if headless:
        # print("Hiding Firefox")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920x1080")
    return webdriver.Firefox(options)


def logo():
    print("""
___________                       _____          __                         __  .__               
\__    ___/______ __ __   ____   /  _  \  __ ___/  |_  ____   _____ _____ _/  |_|__| ____   ____  
  |    |  \_  __ \  |  \_/ __ \ /  /_\  \|  |  \   __\/  _ \ /     \\\\__  \\\\   __\  |/  _ \ /    \ 
  |    |   |  | \/  |  /\  ___//    |    \  |  /|  | (  <_> )  Y Y  \/ __ \|  | |  (  <_> )   |  \\
  |____|   |__|  |____/  \___  >____|__  /____/ |__|  \____/|__|_|  (____  /__| |__|\____/|___|  /
                             \/        \/                         \/     \/                    \/ 
=======================================================================================================
                        Script for scraping Bexar properties
=======================================================================================================""")


if __name__ == "__main__":
    main()
