# reddit-scraper

This porject will scrape selected subreddit for posts and comments and save the data to a postgres database. Using selenium webdriver to load the page and scroll down before scraping using scrapy.

# /reddit/spider/comment.py
Comments.py scapes the subreddit sorted by new to get the urls for each post by scrolling down one full page length (usally around 50 posts scraped). After the list of post urls are created then each is visted using selenium webdriver and sleeps for 5 seconds to give the comments time to load before taking a snapshot of the html. The relevent data is extracted and sent to the pipeline for processing

# /reddit/pipeline.py
The pipeline.py file create the tables to save the reddit post, comments, and subreddit. The raw data is also formated before saving to the database. Items already in the database will be updated to refelect the current values of upvotes, % of upvotes positive/negative, and commentquantity. 


# REQUIRED ENVIROMENT VARIBELS 
  - postgreshost=45.456.456.456
  - postgrespassword=Jfdgdfgdfgg
  - allowed_domains=https://www.reddit.com
  - start_url='https://reddit.com/r/stocks/new'
  - start_url_list=['https://reddit.com/r/stocks/new']
  - subreddit_name=stocks

# LOCAL DEVELOPMENT
You must create .env file with required REQUIRED ENVIROMENT VARIBELS. docker-compose will use a .env and provide postgres connection information and starting urls for the selected subreddit to scrape.

# COMMANDS TO RUN LOCALLY
must have docker installed 
docker-compose build
docker-compose up

# KUBERNETES DEPLOYMENT
The subreddit-scraper-yaml is a cronjob run as a pod. I selected to run this every 3 hours. Each subreddit is scraped in seperate containers before starting the next. This is acomplioshed by using init containers. The postgres connection varibles are loaded from kuberentes secrets for securly injecting enviroment varibles. The url and subreddit information is injected via enviroment vaibles in the yaml file. 

# WARNING
- promoted posts are not scraped
- not all comments are scraped without allowing unlimited recurrion of expanding all comment comments and those comments comments and .......

