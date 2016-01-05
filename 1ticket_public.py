#!/usr/bin/env python
import logging
import csv
import mysql.connector
from mysql.connector import errorcode
import datetime
from datetime import date
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from contextlib import closing
import time
import codecs
import base64
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import schedule
import time
today = date.today()

def download_file():
   #method 'download_file' uses selenium to download a selected file from 1ticket.com
    
    ## setting profile 
    profile = webdriver.FirefoxProfile()
    profile.set_preference('browser.download.folderList', 2);
    profile.set_preference('browser.download.manager.showWhenStarting', False)
    profile.set_preference('browser.download.dir', "/Users/Leon/Desktop/1ticket")
    profile.set_preference('browser.helperApps.neverAsk.openFile','text/csv,application/x-msexcel,application/excel,application/x-excel,application/vnd.ms-excel,image/png,image/jpeg,text/html,text/plain,application/msword,application/xml')
    profile.set_preference('browser.helperApps.neverAsk.saveToDisk','text/csv,application/x-msexcel,application/excel,application/x-excel,application/vnd.ms-excel,image/png,image/jpeg,text/html,text/plain,application/msword,application/xml')
    profile.set_preference('browser.helperApps.alwaysAsk.force', False)
    profile.set_preference('browser.download.manager.alertOnEXEOpen', False)
    profile.set_preference('browser.download.manager.focusWhenStarting', False)
    profile.set_preference('browser.download.manager.useWindow', False)
    profile.set_preference('browser.download.manager.showAlertOnComplete', False)
    profile.set_preference('browser.download.manager.closeWhenDone', False)
    
    ## downloading and saving file to specified location
    logging.info('selenium preferences set - '+str(today))
    driver = webdriver.Firefox(profile)
    driver.implicitly_wait(10)
    driver.get('https://1ticket.com/login.asp')
    logging.info('firefox open successful - '+str(today))
    assert "1ticket.com" in driver.title
    elem = driver.find_element_by_name("fld_username")
    elem.send_keys("username")
    elem1 = driver.find_element_by_name("fld_password")
    elem1.send_keys("password")
    elem1.submit()
    driver.get('https://1ticket.com/tickets_tm.asp');
    logging.info('selenium login successful - '+str(today))
    time.sleep(5) # delays for 5 seconds
    driver.find_element_by_css_selector("a[href*='export']").click();
    driver.implicitly_wait(60)
    time.sleep(45) # delays for 5 seconds
    print(driver.title)
    driver.quit()
    logging.info('selenium driver quit - '+str(today))

def convert_file():
    # method 'convert_file' converts file to readable utf-8 formatting and saves as .txt
    os.system("/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to csv /Users/Leon/Desktop/1ticket/orders.xls")
    os.system("cp orders.csv orders.txt")
    os.system("iconv -f ISO-8859-15 -t UTF-8 orders.txt > ex.txt")
    logging.info('file converted - '+str(today)) 
    os.system("rm /Users/Leon/Desktop/1ticket/orders.xls")
    logging.info('orders.xls removed - '+str(today)) 

def drop_table(cursor):
    # method drops old table table 'matt.orders'
    cursor.execute("drop table 1ticket.orders")
    
    logging.info('table dropped - '+str(today))

def create_table(cursor):    
    # method creates new empty table 'matt.orders'
    cursor.execute("""create table 1ticket.orders  (event_date date,
    event_name varchar(90), quantity int, section varchar(20), row varchar(5), 
    order_cost decimal(12,2), venue varchar(65), purchase_date date)""")
    logging.info('table created - '+str(today))
    cursor.close()

def import_data_from_csv(cursor, cnx, f):
    #method imports txt data to database table, line by line
    logging.info('opening file - '+str(today))
    with open(f, 'r') as f:
        myString = f.read()
    t= myString.splitlines()
    logging.info('importing data - '+str(today))
    for i in t[1:]:
        row = i.split(',')
        while len(row)!=8:
            row[1] = row[1]+row[2]
            del row[2] 
        print row 
        row_0 = row[0]
        row_7 = row[7]
        row[0] = datetime.datetime.strptime(row[0], '%m/%d/%Y').date()
        row[7] = datetime.datetime.strptime(row[7], '%m/%d/%Y').date()
        cursor.execute('INSERT INTO 1ticket.orders (event_date, event_name,\
        quantity, section, row, order_cost, venue, purchase_date)' \
            'VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', 
            row)
        cnx.commit()
    logging.info('data imported! - '+str(today))

def query_nday(cursor, days, limit=20):
    # method recieves a cursor, amount of days, and a limit. the method then runs a query and creates an html
    # string for a table with the sales results of the last 'days' amount of days

    if days == 1:
        title_days ='Yesterday'
    else:
        title_days = 'Last '+str(days)

    #building html table    
    output = ("<b><font size=\"17\"> "+title_days+" Days Sales Summary:</font> </b> <br><br>  \
    <table border=\"1\" style=\"width:100%\"> <tr> <th>Event Date</th>   \
    <th>Event Name</th> <th>Venue</th>  <th>Orders</th>  <th>Tickets</th>  \
    <th>Volume($)</th> </tr>")
    


    #defining and running query
    query = ("select event_date, event_name, venue, count(section) as order_count, \
    sum(quantity) as ticket_quantity, CONCAT('$', FORMAT(sum(order_cost), 2))\
    as  volume from 1ticket.orders where purchase_date > curdate()-"+str(days+1)+" group by  event_date, \
    venue, event_name having order_count > 1 order by order_count desc, ticket_quantity  desc limit "+str(limit))
    cursor.execute(query)


    #adding query results to html string
    for i in cursor:
        output = output + "<tr>"
        for j in i:
            output = output + " <td> " + str(j) +  "</td>"
        output = output + "</tr>"
    output = output +"</table>"
    logging.info ('query '+title_days+' day done - '+str(today))
    return output 

def query_topEvents_by_dollars(cursor, days, limit = 30):
    # method recieves a cursor and a limit. the method then runs a query and creates an html
    # string for a table with the query results for top events sorted by dollars

    # building html table
    output = ("\
    <b><font size=\"17\">Top Events by Volume Last "+str(days)+" Days:</font> </b> <br><br> \
    <table border=\"1\" style=\"width:100%\"> <tr> \
    <th>Event Name</th>  <th>Orders</th>  <th>Tickets</th> \
    <th>Volume($)</th> </tr>")
    

    #defining and running query
    query = ("select event_name, count(section) as orders, sum(quantity) as \
        tickets, CONCAT('$', FORMAT(sum(order_cost), 2)) as volume from \
        1ticket.orders where purchase_date > curdate()-"+str(days+1)+" group by event_name \
        order by sum(order_cost) desc, orders desc limit "+str(limit))
    cursor.execute(query)


    #adding query results to html string
    for i in cursor:
        output = output + "<tr>"
        for j in i:
            output = output + " <td> " + str(j) +  "</td>"
        output = output + "</tr>"
    output = output +"</table>"
    logging.info('top event by volume query done - '+str(today))
    return output
 
def query_topEvents_by_orders(cursor, days, limit=30):
    # method recieves a cursor and a limit. the method then runs a query and creates an html
    # string for a table with the query results for top events sorted by orders

    #building html table
    output = ("\
    <b><font size=\"17\">Top Events by Orders Last "+str(days)+" Days:</font> </b> <br><br> \
    <table border=\"1\" style=\"width:100%\"> <tr> \
    <th>Event Name</th>  <th>Orders</th>  <th>Tickets</th> \
    <th>Volume($)</th> </tr>")

    #defining and running query
    query = ("select event_name, count(section) as order_count, sum(quantity)\
    as ticket_quantity, CONCAT('$', FORMAT(sum(order_cost), 2)) as volume \
    from 1ticket.orders where purchase_date > curdate()-"+str(days+1)+" group by event_name\
    order by order_count desc, ticket_quantity desc limit "+str(limit))
    cursor.execute(query)


    #adding query results to html string
    for i in cursor:
        output = output + "<tr>"
        for j in i:
            output = output + " <td> " + str(j) +  "</td>"
        output = output + "</tr>"
    output = output +"</table>"
    logging.info('top events by orders query done - '+str(today))
    return output

def email(to, subject, body): 
    # method takes to address, subject, and body to send email

    fromaddr = "from email address"
    toaddr = "to email address"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = to 
    msg['Subject'] = subject
    part2 = MIMEText(body, 'html')
    msg.attach(part2)
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    pw = "password"
    server.login(fromaddr, pw)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    logging.info('email ('+subject+' ) sent to '+ to+' - '+str(today))
    server.quit()


##Main
def main():
    
    download_file()
    convert_file()
    today = date.today()
    LOG_FILENAME = 'logging_file.txt'
    logging.basicConfig(filename=LOG_FILENAME,
                        level=logging.DEBUG,)


    data_file = '/Users/Leon/ex.txt'
    cnx = mysql.connector.connect(user='root', password='password',
                            host='127.0.0.1',
                            database='1ticket')                            
    logging.info('connected to db - '+str(today))
    cursor = cnx.cursor()
    # import data to table
    """
    with closing( cnx.cursor() ) as cursor:
        drop_table(cursor)
    with closing( cnx.cursor() ) as cursor:
        create_table(cursor)
    with closing( cnx.cursor() ) as cursor:    
        import_data_from_csv(cursor, cnx, data_file)
"""
        
    # run queries
    with closing( cnx.cursor() ) as cursor:    
        table_1day = query_nday(cursor, 1)    
    with closing( cnx.cursor() ) as cursor:    
        table_10day = query_nday(cursor, 14)       
    with closing( cnx.cursor() ) as cursor:        
        table_30day = query_nday(cursor, 30)     
    with closing( cnx.cursor() ) as cursor:  
        table_topPerformer = query_topEvents_by_dollars(cursor, 60)   
    with closing( cnx.cursor() ) as cursor:  
        table_topEvent = query_topEvents_by_orders(cursor, 60)    
    # email setup
    body1 = table_1day+ "<br><br>"+table_10day+"<br><br>"+table_30day   
    to = 'to email'
    subject = 'Ticketmaster Purchase Report'
    email(to, subject, body1)
    body2 = table_topPerformer + "<br><br>"+table_topEvent
    email(to, subject, body2)
    cursor.close()
    logging.info('cursor closed - '+str(today))
    cnx.close()
    logging.info('connection closed - '+str(today))

if __name__ == '__main__': 
    main()


