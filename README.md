
﻿# reddit-scraper

This project will scrape selected subreddit for posts and comments and save the data to a postgres database. Using selenium webdriver to load the page and scroll down before scraping using scrapy.

# /reddit/spider/comment.py
Comments.py scapes the subreddit sorted by new to get the urls for each post by scrolling down one full page length (usually around 50 posts scraped). After the list of post urls are created then each is visited using selenium webdriver and sleeps for 5 seconds to give the comments time to load before taking a snapshot of the html. The relevant data is extracted and sent to the pipeline for processing

# /reddit/pipeline.py
The pipeline.py file creates the tables to save the reddit post, comments, and subreddit. The raw data is also formatted before saving to the database. Items already in the database will be updated to reflect the current values of upvotes, % of upvotes positive/negative, and comment quantity. 


# REQUIRED ENVIRONMENT VARIABLES 
  - postgreshost=45.456.456.456
  - postgrespassword=Jfdgdfgdfgg
  - allowed_domains=https://www.reddit.com
  - start_url='https://reddit.com/r/stocks/new'
  - start_url_list=['https://reddit.com/r/stocks/new']
  - subreddit_name=stocks

# LOCAL DEVELOPMENT
You must create .env file with required REQUIRED ENVIRONMENT VARIABLES. docker-compose will use a .env and provide postgres connection information and starting urls for the selected subreddit to scrape.

# COMMANDS TO RUN LOCALLY
- docker-compose build
- docker-compose up

# KUBERNETES DEPLOYMENT
The subreddit-scraper-yaml is a cron job run as a pod. I selected to run this every 3 hours. Each subreddit is scraped in separate containers before starting the next. This is accomplished by using init containers. The postgres connection variables are loaded from kubernetes secrets for securly injecting environment variables. The url and subreddit information is injected via environment variables in the yaml file. 


# WARNING
- must have docker installed 
- .env file created in root of the repository folder
- promoted posts are not scraped
- not all comments are scraped without allowing unlimited recursion of expanding all comment comments and those comments comments and .......
- must provide REQUIRED ENVIRONMENT VARIABLES
- when running kubernetes cronjob must create secret with postgres connection string and password

