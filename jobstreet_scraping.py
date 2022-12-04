# Libraries
import scrapy # Use for Web Scraping
import time # Use to add daley on request
import json  # To read json object
from datetime import datetime, timedelta  # Use in Date   
from scrapy.crawler import CrawlerProcess # To run the scraping


class JobStreetSpider(scrapy.Spider):
    """ JobStreet Scraping """
    name = "jobstreet_jobs"

    def start_requests(self):
        """ Start Request Page"""
        # Paramters
        keyword_list = ["software-developer"]
        location_list = ['taguig']

        # Request URL with parameters
        for keyword in keyword_list:
            for location in location_list:
                jobstreet_jobs_url = f"https://www.jobstreet.com.ph/en/job-search/{keyword}-jobs-in-{location}/"
                yield scrapy.Request(url=jobstreet_jobs_url, callback=self.parse_pagination, meta={"keyword": keyword, "location": location})

    def parse_pagination(self, response):
        """ Parsing Pagination in JobStreet"""
        # Fetch current Keywords and Location
        keyword = response.meta['keyword'] 
        location = response.meta['location']

        # Determine number of pages
        pagination = response.css("select#pagination>option::attr(value)").extract()  
        # loop ever pages
        for page in range(1, int(pagination[1])): 
            page_url = f"https://www.jobstreet.com.ph/en/job-search/{keyword}-jobs-in-{location}/{page}/"
            yield scrapy.Request(url=page_url, callback=self.parse_page_result, dont_filter=True)
        # dont_filter - The class used to detect and filter duplicate requests. 
                        # If true = Dont filter duplicates and False to remove

    def parse_page_result(self, response):
        """Parsing Each Job link"""
        job_link = response.xpath("//h1[contains(@class, 'sx2jih0 zcydq84u _18qlyvc0 _18qlyvc1x _18qlyvc3 _18qlyvca')]/a/@href").extract()
        # Loop thru each pages
        for link in job_link:
            url = f"https://www.jobstreet.com.ph{link}"
            time.sleep(1) # To Prevent Request time error
            yield scrapy.Request(url=url, callback=self.parse_jobpage, meta={'link': url})
        
        
    def parse_jobpage(self, response):
        """ Parsing the jobpage and fetch result"""
        divpath = "div[@class='sx2jih0 zcydq86a']"  # Creating Short path for div

        # ============= PARAMETERS NEEDED ============
        # Job Title
        job_title = response.xpath("//h1[contains(@class, 'sx2jih0 _18qlyvc0 _18qlyvch _1d0g9qk4 _18qlyvcp _18qlyvc1x')]/text()").extract_first()
        
        # Company Name
        company = response.xpath("//div[@class='sx2jih0 zcydq86m']/span/text()").extract_first()
        
        # Job Location
        location = response.xpath(f"//{divpath}/div[@class='sx2jih0 zcydq856']/span/text()").extract_first()
        if location is None:
            location = response.xpath(f"//{divpath}/div/div/div[@class='sx2jih0 zcydq86i zcydq87i mFVxF']/span/text()").extract()
        
        
        # Determining Date or salary(DOS)
        # Salary and Date Posted
        dos = response.xpath(f"//{divpath}/span[@class='sx2jih0 zcydq84u _18qlyvc0 _18qlyvc1x _18qlyvc1 _18qlyvca']/text()").extract()
        if len(dos) == 2:
            salary = dos[0]
            raw_date = dos[1]
        else: 
            # If Salary is not available
            salary = None
            raw_date = dos[0]
        
        # Fix format Date
        split_date = raw_date.split(" ")
        if len(split_date) > 3:
            # split_date = [Posted, 5, hours, ago]
            date = datetime.now() - timedelta(hours=int(split_date[1]))
        else:
            # split_date = [Posted, on, 22-Nov-22]
            date = datetime.strptime(split_date[2],'%d-%b-%y').date()
            

        # Job Summary
        raw_summary = response.css("div.YCeva_0>span>div.sx2jih0 ::text").extract()
        clean_summary = [summary.strip() for summary in raw_summary if len(summary.strip()) > 0]  # Cleaning white spaces
        summary = " ".join(clean_summary) # Combining the sentences into one paragrahp
        

        # Tools
        dev_tools = {
            "Prog_scripting_markup_languages" : [],
            "databases" : [],
            "frameworks_web_dev": [],
            "frameworks_mobile_dev" : [],
            "other_frameworks_and_libraries" : [],
            "other_tools" : [],
            "IDLE" : [],
            "asynchronous_tools" : [],
            "synchronous_tools" : [],
            "OS" : [],
            "CMS_tools" : [],
            "CRM_tools" : [],
            "methodologies" : [],
            "cloud_platforms" : [],
            "version_control_platforms" : [],
        }

       # Opening JSON file
        with open('developers_tools.json', encoding='utf-8') as dt:
            # Convert to json object
            dt_data = json.load(dt)

            # Iterating through the json
            for key, value in dt_data.items():  
                # Cleaning summary word by word
                words = summary.lower().replace("(", "").replace(")", "").replace(",", "").split(" ")
                
                # Loop thru all tools
                for v in value:
                    v_low = v.lower()  # Transform value into lower case text
                    v_split = v_low.split(" ") # Split the tools by words

                    # For two or more word tools
                    if len(v_split) > 1:
                        # Loop thru all words that matches the values
                        for i in range(len(words)):
                            if words[i:i+len(v_split)] == v_split:
                                dev_tools[key].append(v)  # Save tool
                                break  # Exit loop

                    # For one word tools               
                    else: 
                        # Check if value == words
                        if v_low in words:
                            dev_tools[key].append(v) # Save tool

        # Fetch Additional Information(A.I)
        fetch_ai = response.xpath("//div[@class='sx2jih0 _17fduda0 _17fduda7']/div/div/div/div/div/span//text()").extract() 
        
        # Cleaning the fetch_ai 
        clean_ai = [item.replace(',', "") for item in fetch_ai] # Removing ',' into blank space
        clean_ai.remove(" ")  # Removing blank space
        select_ai = clean_ai[:11]  # Selecting specific data

        # Combine the 1st and 2nd last value for Job Specialization value
        select_ai.append([select_ai.pop(), select_ai.pop()]) 

        # Getting and Storing the needed data for A.I
        additional_info = {select_ai[i]:select_ai[i+1] for i in range(0, len(select_ai), 2)}
            
        # Fix Career level format
        raw_career_lvl = additional_info.get('Career Level', None)
        if raw_career_lvl:
            split_career_lvl = raw_career_lvl.split(" ")
            if len(split_career_lvl) == 4:
                # split_career_lvl = [1-4, Years, Experienced, Employee]
                career_lvl = f"{split_career_lvl[0]} yrs"
            elif len(split_career_lvl) == 6:
                # split_career_lvl = [Less, than, 1, Year, Experienced, Employee]
                career_lvl = '0-1 yr'
            else:
                # Other format
                career_lvl = raw_career_lvl
        else:
            # Return None
            career_lvl = raw_career_lvl

        

        # Save Parameters
        yield {
                "job_title": job_title,
                "company": company,
                "location": location,
                "salary": salary,
                "Prog_scripting_markup_languages": dev_tools.get("Prog_scripting_markup_languages", None),
                "databases": dev_tools.get("databases", None),
                "frameworks_web_dev": dev_tools.get("frameworks_web_dev", None),
                "frameworks_mobile_dev": dev_tools.get("frameworks_mobile_dev", None),
                "other_frameworks_and_libraries": dev_tools.get("other_frameworks_and_libraries", None),
                "other_tools": dev_tools.get("other_tools", None),
                "IDLE": dev_tools.get("IDLE", None),
                "asynchronous_tools": dev_tools.get("asynchronous_tools", None),
                "synchronous_tools": dev_tools.get("synchronous_tools", None),
                "OS": dev_tools.get("OS", None),
                "CMS_tools": dev_tools.get("CMS_tools", None),
                "CRM_tools": dev_tools.get("CRM_tools", None),
                "methodologies": dev_tools.get("methodologies", None),
                "cloud_platforms": dev_tools.get("cloud_platforms", None),
                "version_control_platforms": dev_tools.get("version_control_platforms", None),
                "date_posted": date.strftime("%d-%m-%Y %H:%M:%S"),
                "career_level": career_lvl,
                "qualification": additional_info.get('Qualification', None),
                "years_of_experience": additional_info.get('Years of Experience', None),
                "job_specializations": additional_info.get('Job Specializations', None),
                "link": response.meta['link'],
                "summary": summary           
            }


# Setting  up the Crawler settings
process = CrawlerProcess(
    settings={
        "FEEDS": {
            "jobsteet_data.json": {"format": "json", 'overwrite': True},
        }
    }

)
process.crawl(JobStreetSpider)  # Defining Spider name
process.start() # Start the crawler process
