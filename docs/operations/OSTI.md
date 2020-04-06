# Manually submit a DOI to OSTI

There are two methods:
   1. OSTI web page
   2. curl
 
## To  submit record(s) via web page API in either XML or JSON format
 
1. In a browser enter:   https://www.osti.gov/iad2test
2. click on Upload Request
3. click on Browse to locate file to be submitted -- enter credentials
4. success or failure ?
 
 

### To  submit record to test server in XML format
 
    curl -u <login>:<password> https://www.osti.gov/iad2test/api/records -X POST -H "Content-Type: application/xml" -H "Accept: application/xml" --data @ATMOS_LADEE_NMS_Bundle_DOI_label_20180911.xml
 

### To  submit record to test server in JSON format
 
    curl -u <login>:<password> https://www.osti.gov/iad2test/api/records -X POST -H "Content-Type: application/json" -H "Accept: application/json" --data @ATMOS_LADEE_NMS_Bundle_DOI_label_20180911. Json
 
Curl will return either success or failure.  An email will sent with the status. 
 
# Email 

Ask Steph to update the email distribution list.

We might also consider giving them separate credentials so that we all don’t get overrun by emails.

**Contact:** 

    Stephanie Gerics
    Office of Scientific and Technical Information (OSTI)
    US Department of Energy
    gericss@osti.gov
    (865) 241-9653
