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
    logging.info(datetime.datetime.now().isoformat()+' - selenium preferences set')
    driver = webdriver.Firefox(profile)
    driver.implicitly_wait(10)
    driver.get('https://1ticket.com/login.asp')
    logging.info(datetime.datetime.now().isoformat()+' - firefox open successful')
    assert "1ticket.com" in driver.title
    elem = driver.find_element_by_name("fld_username")
    user = 'your username here'
    pw = 'your password here'
    elem.send_keys(user)
    elem1 = driver.find_element_by_name("fld_password")
    elem1.send_keys(pw)
    elem1.submit()
    driver.get('https://1ticket.com/tickets_tm.asp');
    logging.info(datetime.datetime.now().isoformat()+' - selenium login successful')
    time.sleep(5) # delays for 5 seconds
    driver.find_element_by_css_selector("a[href*='export']").click();
    driver.implicitly_wait(60)
    time.sleep(45) # delays for 5 seconds
    print(driver.title)
    driver.quit()
    logging.info(datetime.datetime.now().isoformat()+' - selenium driver quit')

def convert_file(file):
    # method 'convert_file' converts file to readable utf-8 formatting and saves as .txt, 
    # then removes .xls file
    os.system("/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to csv "+file)
    os.system("cp orders.csv orders.txt")
    os.system("iconv -f ISO-8859-15 -t UTF-8 orders.txt > /Users/Leon/Desktop/1ticket/ex.txt")
    logging.info(datetime.datetime.now().isoformat()+' - file converted')
    os.system("rm /Users/Leon/Desktop/1ticket/orders.xls")
    logging.info(datetime.datetime.now().isoformat()+' - orders.xls removed')

def drop_table(cursor):
    # method drops old table table 'matt.orders'
    cursor.execute("drop table 1ticket.orders")
    logging.info(datetime.datetime.now().isoformat()+' - table dropped')

def create_table(cursor):    
    # method creates new empty table 'matt.orders'
    cursor.execute("""create table 1ticket.orders  (event_date date,
    event_name varchar(90), quantity int, section varchar(20), row varchar(5), 
    order_cost decimal(12,2), venue varchar(65), purchase_date date)""")
    logging.info(datetime.datetime.now().isoformat()+' - new table created')
    cursor.close()

def import_data_from_csv(cursor, cnx, f):
    #method imports txt data to database table, line by line
    logging.info(datetime.datetime.now().isoformat()+' - opening file')
    with open(f, 'r') as f:
        myString = f.read()
    t= myString.splitlines()
    logging.info(datetime.datetime.now().isoformat()+' - importing file')
    for i in t[1:]:
        row = i.split(',')
        while len(row)!=8:
            row[1] = row[1]+row[2]
            del row[2] 
        row_0 = row[0]
        row_7 = row[7]
        row[0] = datetime.datetime.strptime(row[0], '%m/%d/%Y').date()
        row[7] = datetime.datetime.strptime(row[7], '%m/%d/%Y').date()
        cursor.execute('INSERT INTO 1ticket.orders (event_date, event_name,\
        quantity, section, row, order_cost, venue, purchase_date)' \
            'VALUES(%s, %s, %s, %s, %s, %s, %s, %s)', 
            row)
        cnx.commit()
    logging.info(datetime.datetime.now().isoformat()+' - data imported!')

def query_nday(cursor, days, limit=20):
    #method recieves a mySQL cursor, an amount of days 'days', and a limit of results 'limit'
    #  with those arguments, this method will return a table in the form of html string, containing
    # sales data (featuring sales by events) for the trailing 'days' sorted by order count

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
    logging.info(datetime.datetime.now().isoformat()+" - query "+title_days+" day done")
    return output 

def query_topEvents_by_dollars(cursor, days, limit = 30):
    #method recieves a mySQL cursor, an amount of days 'days', and a limit of results 'limit'
    #  with those arguments, this method will return a table in the form of html string, containing
    # sales data (featuring sales by performer) for the trailing 'days' sorted by revenue

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
    logging.info(datetime.datetime.now().isoformat()+" - top event by volume query done")
    return output
 
def query_topEvents_by_orders(cursor, days, limit=30):
    #method recieves a mySQL cursor, an amount of days 'days', and a limit of results 'limit'
    #  with those arguments, this method will return a table in the form of html string, containing
    # sales data (featuring sales by performer) for the trailing 'days' sorted by order count

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
    logging.info(datetime.datetime.now().isoformat()+" - top event by order query done")
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
    pw = 'email password'
    server.login(fromaddr, pw)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    logging.info(datetime.datetime.now().isoformat()+" - email ("+subject+" ) sent to "+ to+" - '")
    server.quit()


##Main
def main():
    # main method downloads data from 1ticket, converts file to readable format, then imports data to mysql db
    # after that, main will run various queries that return different splits sales data in html tables
    # main will then email out the data tables
    # **logging data is created and placed in file called '1_ticket_logging_file.txt**'
    logging.info(datetime.datetime.now().isoformat()+' - process started')
    file_xls = '/Users/Leon/Desktop/1ticket/orders.xls'
    

    #download_file()
    #convert_file(file_xls)
    today = date.today()
    LOG_FILENAME = '1ticket_logging_file.txt'
    logging.basicConfig(filename=LOG_FILENAME,
                        level=logging.DEBUG,)


    data_file = '/Users/Leon/Desktop/1ticket/ex.txt'
    pw = 'mysql password'
    cnx = mysql.connector.connect(user='root', password=pw,
                            host='127.0.0.1',
                            database='matt')                            
    logging.info(datetime.datetime.now().isoformat()+' - connected to db')
    cursor = cnx.cursor()
    # import data to table
    
    with closing( cnx.cursor() ) as cursor:
        drop_table(cursor)
    with closing( cnx.cursor() ) as cursor:
        create_table(cursor)
    with closing( cnx.cursor() ) as cursor:    
        import_data_from_csv(cursor, cnx, data_file)

        
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
    to = 'to email address here'
    subject = 'Ticketmaster Purchase Report'
    email(to, subject, body1)
    body2 = table_topPerformer + "<br><br>"+table_topEvent
    email(to, subject, body2)
    cursor.close()
    logging.info(datetime.datetime.now().isoformat()+' - cursor closed')
    cnx.close()
    logging.info(datetime.datetime.now().isoformat()+' - connection closed')
    logging.info(datetime.datetime.now().isoformat()+' - process completed \n')

if __name__ == '__main__': 
    main()

