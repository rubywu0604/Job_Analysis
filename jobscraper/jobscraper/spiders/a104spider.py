import scrapy
import re
import json
import requests
from bs4 import BeautifulSoup
from jobscraper.items import JobscraperItem


class A104spiderSpider(scrapy.Spider):
    name = "104spider"
    allowed_domains = ["www.104.com.tw"]

    def start_requests(self):
        job_types = [
            "ios_engineer_工程師", "android_engineer_工程師", "frontend_engineer_前端工程師", 
            "backend_engineer_後端工程師", "data_engineer_資料工程師", "data_analyst_資料分析師", 
            "data_scientist_資料科學家", "dba_資料庫管理"
        ]
        for job_type in job_types:
            for p in range(1, 51):
                url = f"https://www.104.com.tw/jobs/search/?keyword={job_type}&page={p}"
                yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        jobs = response.css('article.job-list-item')
        for job in jobs:
            lastupdate = job.css('h2 span.b-tit__date::text').get().strip()
            if "/" in lastupdate:
                category = re.search(r'keyword=(\w+)_', response.url).group(1)
                job_title = job.css('h2 a::text, h2 em::text').getall()
                job_title = ''.join(job_title).strip()
                location = job.css('ul.job-list-intro li:nth-child(1)::text').get()
                company = job.css('li:nth-child(2) a::text').get().strip().replace('\n', '')
                salary = job.css('div.job-list-tag a:nth-child(1)::text').get()
                education = job.css('ul.job-list-intro li:nth-child(5)::text').get()
                experience = job.css('ul.job-list-intro li:nth-child(3)::text').get()
                job_link = 'https:' + job.css('h2 a::attr(href)').get()
                yield scrapy.Request(
                    job_link,
                    callback=self.parse_104_details,
                    meta={
                        'category': category,
                        'job_title': job_title,
                        'location': location,
                        'company': company,
                        'salary': salary,
                        'education': education,
                        'experience': experience,
                        'job_link': job_link
                    }
                )

    def parse_104_details(self, response):
        job_link = response.url
        req = requests.get(job_link)
        soup = BeautifulSoup(req.text, 'html.parser')
        job_description = soup.text.lower()
        job_description_cleaned = re.sub(r'\s+', '', job_description)
        conditions = [
            "python", "ios", "swift", "android", "ruby", "c#", "c++", "php", "jquery", "aws",
            "typescript", "scala", "julia", "objective-c", "numpy", "pandas", "tensorflow", "gcp",
            "pytorch", "opencv", "react", "angular", "ruby on rails", ".net", "hibernate", "redis", 
            "express.js", "rubygems", ".net core", "django", "mysql", "ajax", "html", "css", "kotlin",
            "postgresql", "mongodb", "sqlite", "cassandra", "django", "express.js", "golang", "spark", 
            "flask", "react", "vue.js", "asp.net", "docker", "kubernetes", "flutter", "restful api",
            "azure", "ibm cloud", "node.js", "firebase", "airflow", "github","arduino", "power bi",
            "hadoop", "kafka", "elasticsearch", "tableau", "splunk", "scikit-learn"
        ]

        java_pattern = re.search(r'(java)\W', job_description)
        javascript_pattern = re.search(r'(?<!without )(javascript)', job_description)

        special_case_java = java_pattern.group(1) if java_pattern else None
        special_case_javascript = javascript_pattern.group(1) if javascript_pattern else None

        skill_set = set()
        for condition in conditions:
            if condition in job_description_cleaned:
                skill_set.add(condition)
            elif special_case_java:
                skill_set.add(special_case_java)
            elif special_case_javascript:
                skill_set.add(special_case_javascript)
        
        a104Item = JobscraperItem()

        a104Item['category'] = response.meta.get('category')
        a104Item['job_title'] = response.meta.get('job_title')
        a104Item['location'] = response.meta.get('location')
        a104Item['company'] = response.meta.get('company')
        a104Item['min_monthly_salary'] = response.meta.get('salary')
        a104Item['max_monthly_salary'] = response.meta.get('salary')
        a104Item['education'] = response.meta.get('education')
        a104Item['experience'] = response.meta.get('experience')
        a104Item['job_link'] = response.meta.get('job_link')
        a104Item['skills'] = "Null" if skill_set == set() else list(skill_set)
        a104Item['source_website'] = "104人力銀行"
        
        yield a104Item