import os
import sys
import time
import socket
import random #delays inevitability of captcha
from selenium import webdriver #Browser automation
from selenium.webdriver.support.ui import Select #selects items
from selenium.webdriver.chrome.options import Options #google chrome options
from selenium.common.exceptions import NoSuchElementException #for captcha

def restart():
    os.execv(sys.executable, ['python'] + sys.argv) #one liner to restart without recompiling

def determine_valid_ip(address):
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        return False

def parse_for_domain(url): #finds domain name from relative url
    if(url.count('.') == 1 or url.count('.') < 1): # base case
        return url
    else:
        return parse_for_domain(url[url.find('.') + 1:]) #recurse to find next period

def read_domains(input_domain_file, output_domain_file):
    port_num = 0
    with open(input_domain_file, "r") as f:
        domain_list = set()
        for line in f:
            url = line.rstrip("\n")
            #check HERE if a url from a text file is indeed some sort of IP address with possibly a port, otherwise strip the periods off
            if(any(c.isalpha() for c in url) == False): #checks for letters
                portnum = url.find(":")
                if(portnum != -1): #checks for portnum
                    ip_no_port = url[:portnum]
                    if(determine_valid_ip(ip_no_port)): #string from ip address which excludes portnum
                        domain_list.add(url)
                else:
                    if(determine_valid_ip(url)):
                        domain_list.add(url)
            else:
                print(url+","+parse_for_domain(url)) 
                domain_list.add(parse_for_domain(url))

    with open(output_domain_file, "w") as f:
        f.seek(0)
        for domain in domain_list:
            f.write(domain)
            f.write("\n")

    return domain_list

def remove_domain_from_list(filtered_domain_list, domain_list_name):
    with open(filtered_domain_list, "r") as f:
        lines = f.readlines()

    with open(filtered_domain_list, "w") as f:
        for line in lines:
            if (line.strip("\n") != domain_list_name):
                f.write(line)

def remove_url_from_list(url_list, url_list_name):
   with open(url_list, "r+") as f:
    urls = f.readlines()
    f.seek(0)
    for url in urls:
        if(url.find(url_list_name) == -1):
            f.write(url)
    f.truncate()

def start_driver(domain_name):

    url = 'https://sitereview.bluecoat.com/#/'
    driver_path = "C:\\Users\\Modima\\AppData\\Local\\Programs\\Python\\Python37\\Scripts\\chromedriver.exe"

    options = Options()
    options.add_argument("--log-level=3")  #disables/suppresses chrome error warnings for selenium
    options.add_experimental_option('excludeSwitches', ['enable-logging']) #disables "Dev Tools listening"..."

    driver = webdriver.Chrome(driver_path, options=options)
    driver.get(url)
    driver.minimize_window() #For maximizing window

    # page 1 - type in url and fill in text box with id number with description of the incident, then proceed to next page
    try:

        driver.find_element_by_id("txtSearch").clear()
        time.sleep(3)
        driver.find_element_by_id('txtSearch').send_keys(domain_name)
        time.sleep(1)
        driver.find_element_by_id("btnLookupSubmit").click()
        time.sleep(1)
        driver.find_element_by_id("btnLookupSubmit").click()
        time.sleep(random.randrange(5,15,1))

    #page 2
        file = open("output_file.txt", 'a+')
        categorizations = driver.find_elements_by_class_name('clickable-category')
        first_categorization = driver.find_element_by_class_name('clickable-category').text
        second_categorization = ""
        review_date = driver.find_element_by_class_name('rating-date').text

        if (len(categorizations) == 2):
            second_categorization = categorizations[1].text
            file.write(domain_name + "," + first_categorization + "," + second_categorization + "," + review_date[26: len(review_date)-1])
            file.write("\n")
        
        else:
            file.write(domain_name + "," + first_categorization + "," + review_date[26: len(review_date)-1])
            file.write("\n")
        file.close()            
        driver.close()
        
    except NoSuchElementException:
        print("Inputted domain has an exception : ", domain_name)
        try:
            if(driver.find_element_by_class_name('suggestion').text.find("shortening") != -1):
                print("Reason: URL shortening service\n")
                f = open("output_file.txt", "a+")
                f.write(domain_name + ",URL shortening service,-")
                f.write("\n")
                f.close()
                remove_url_from_list("domains.txt", domain_name)
                remove_domain_from_list("filtered_input.txt", domain_name)
                time.sleep(3)
                restart()
        except NoSuchElementException:
            pass
        
        try:
            if(driver.find_element_by_class_name('mat-dialog-content').text.find("TLD") != -1):
                print("Reason: URL is not a TLD (Top-Level-Domain)\n")
                file = open("error_inputs.txt", "a+")
                file.write(domain_name + " is not a TLD")
                file.write("\n")
                remove_url_from_list("domains.txt", domain_name)
                remove_domain_from_list("filtered_input.txt", domain_name)
                time.sleep(3)
                restart()
        except NoSuchElementException:
            pass

        try:
            if(driver.find_element_by_class_name('emphasis').text == "Since this URL has not yet been rated"):
                print("Reason: Currently not rated\n")
                file = open("output_file.txt", "a")
                file.write(domain_name + ",not been rated by Symantec SiteReview,-")
                file.write("\n")
                remove_url_from_list("domains.txt", domain_name)
                remove_domain_from_list("filtered_input.txt", domain_name)
        except NoSuchElementException:
            pass

        try:
            if(driver.find_element_by_class_name('mat-dialog-content').text.find("resolve") != -1):
                print("Reason: Unresolvable Host\n")
                f = open("error_inputs.txt", "a+")
                print("Unresolvable URL Host : ", domain_name)
                f.write(domain_name)
                f.write("\n")
                remove_url_from_list("domains.txt", domain_name)
                remove_domain_from_list("filtered_input.txt", domain_name)  
                time.sleep(3)
                restart()
        except NoSuchElementException:
            pass 
        
        try:
            if(bool(driver.find_element_by_id('imgCaptcha')) == True):
                print("Reason: CAPTCHA appeared! Please fill in and try again later!")
                time.sleep(3)
                quit()
        except NoSuchElementException:
            pass
            
def main():

    if(os.stat("domains.txt").st_size == 0):
        print("There is nothing left to submit! Please populate text files with URLS and try again! :)")
        sys.exit(0)

    else:
        error_domains = set()
        domain_list = set()
        domain_list = read_domains("domains.txt", "filtered_input.txt")
        
        for domain in domain_list:

            if(domain[0:3] == "10."): #internal ip
                f = open("output_file.txt", "a+")
                f.write(domain + ",Internal IP address,-")
                f.write("\n")
                remove_url_from_list("domains.txt", domain)
                remove_domain_from_list("filtered_input.txt", domain)

            if(domain.count(".") < 1 or len(domain) < 4 or len(domain) -1 == "."):
                error_domains.add(domain)
                f = open("error_inputs.txt", "a+")
                for error in error_domains:
                    print(error)
                    f.write(error)
                    f.write("\n")
                remove_url_from_list("domains.txt", error)
                remove_domain_from_list("filtered_input.txt", error)
            
            else:
                start_driver(domain)
                print("Domain for submission: ", domain)
                print("Submission Successful!\n")
                remove_url_from_list("domains.txt", domain)
                remove_domain_from_list("filtered_input.txt", domain)
    
if __name__ == "__main__":
    print("\nAUTOMATED BULK SYMANTEC WEB URL CHECKER:")
    print("----------------------------------------")
    main()
    print("All domains succesfully submitted and logged in output!")
    sys.exit(0)