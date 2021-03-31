# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from datetime import datetime, timedelta
from textblob import TextBlob
import os
import nltk
import numpy as np
import time
nltk.download('punkt')

class RedditPipeline:
    def open_spider(self, spider):
        #connect to database
        self.conn = psycopg2.connect(
                host= os.getenv('postgreshost'),
                database="postgres",
                user="postgres",
                password=os.getenv('postgrespassword'))
        self.conn.autocommit=True

        self.curr = self.conn.cursor()
        #create table for post
        self.create_subreddit_table_db()
        self.create_post_table_db()
        self.create_comment_table_db()
        self.create_post_comment_last_saved_tables() # used to save datetime of OLDEST updated vlaue


    def process_item(self, item, spider):
        ######### POSTS PROCESSING#########
        postTitle = item['postTitle']
        postUserName = item['postUserName']
        postText = item['postText']
        postTimeSince = item['postTimeSince']
        postUpVotes = item['postUpVotes']
        postPercentUpVotes = item['postPercentUpVotes']
        commentQuanity = len(item['comments'])
        self.subreddit_name = item['subreddit_name']
        self.save_subreddit_db()
        # commbine postText paragraphs into one string
        postText = self.combine_paragraphs(postText)
        # create time stamp
        postDateTime = self.time_since_to_date(postTimeSince)
        #format the post votes to int
        postUpVotes = self.upVotesFormater(postUpVotes)
        postPercentUpVotes = self.postPercentUpVotesFormater(postPercentUpVotes)

        ######################
        ######################
        self.curr.execute("""SELECT * FROM redditpost
                        WHERE title=(%s)""", (postTitle,))
        post_qury = self.curr.fetchone()
        self.save_post_db(post_qury=post_qury,
                        postTitle=postTitle,
                        postUserName=postUserName,
                        postUpVotes=postUpVotes,
                        postPercentUpVotes=postPercentUpVotes,
                        commentQuanity=commentQuanity,
                        postText=postText,
                        postDateTime=postDateTime,
                        )
        #########COMMENTS#########
        self.curr.execute("""SELECT id FROM redditpost 
                            WHERE title=%s  ;"""
                                ,(str(postTitle), ))
        postid =  self.curr.fetchone()[0]
     
        for comment in item['comments']:
            # get the post object that the comment is for
            comment['commentUserName']
            commentUpVotes = self.commentUpVotes_formatter(UpVotes=comment['commentUpVotes'])
            commentTimeSince = self.time_since_to_date(comment['commentTimeSince'])
            commentText = self.combine_paragraphs(comment['commentText'])

            self.save_comment_db( username=comment['commentUserName'],
                                commentUpVotes= commentUpVotes,
                                commentTimeSince = commentTimeSince,
                                commentText= commentText,
                                postid = postid)
                            

        return item

    def _save_upload_date(self):
        #save the last upload dates
        self.curr.execute("""SELECT * FROM redditlastpostupdate WHERE subreddit=(%s) """,(self.subreddit_name,))
        existing_time = self.curr.fetchone()
        if existing_time:
            self.curr.execute(""" UPDATE redditlastpostupdate SET
                     datetime=%s,
                     subreddit=%s""",(self.post_time_saved, self.subreddit_name,))
        else:
            print('first time saving post update date')
            self.curr.execute("""INSERT INTO redditlastpostupdate (datetime, subreddit) VALUES (%s, %s)""", 
                            (self.post_time_saved, self.subreddit_name))
        
        self.curr.execute("""SELECT * FROM redditlastcommentupdate WHERE subreddit=(%s) """,(self.subreddit_name,))
        existing_time = self.curr.fetchone()
        if existing_time:
            self.curr.execute(""" UPDATE redditlastcommentupdate SET 
                    datetime=%s,
                    subreddit=%s""",(self.comment_time_saved, self.subreddit_name,))
        else:
            print('first time saving comment update date')
            self.curr.execute("""INSERT INTO redditlastcommentupdate (datetime, subreddit) VALUES (%s, %s)""",
                             (self.comment_time_saved, self.subreddit_name))

    def close_spider(self, spider):
        self._save_upload_date()
        self.conn.close()
        self.curr.close()
    
    def create_subreddit_table_db(self):
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditsubreddit (
                id serial,
                subreddit varchar(255) NOT NULL,
                UNIQUE(subreddit)
            );""")

    def create_post_table_db(self):
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditpost (
                id serial,
                title varchar(10000) NOT NULL,
                username varchar(255) NOT NULL,
                upvotes int NOT NULL,
                percentupvotes int NOT NULL,
                commentquanity int NOT NULL,
                posttext varchar(10000),
                datetime timestamp NOT NULL,
                subreddit varchar(255) references redditsubreddit(subreddit),
                PRIMARY KEY(id),
                CONSTRAINT fk_redditsubreddit
                    FOREIGN KEY(subreddit)
                        REFERENCES redditsubreddit(subreddit)
            );""")

    def create_comment_table_db(self):
        # create table for comments
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditcomment (
                postid int references redditpost(id),
                id serial PRIMARY KEY,
                commentusername varchar(255) NOT NULL,
                upvotes int,
                commenttext varchar(10000),
                datetime timestamp NOT NULL,
                subreddit varchar(255) references redditsubreddit(subreddit),
                CONSTRAINT fk_redditpost
                    FOREIGN KEY(postid)
                        REFERENCES redditpost(id)
            );""")

    def commentUpVotes_formatter(self,UpVotes):
        if UpVotes == "Vote" or UpVotes is None:
            UpVotes = 0
        elif UpVotes[-1]=='k':
            UpVotes = float(UpVotes[:-1]) * 1000
        return int(UpVotes)

    def save_subreddit_db(self):
        self.curr.execute("""SELECT * FROM redditsubreddit
                WHERE subreddit=(%s)""", (self.subreddit_name,))
        subreddit_qury = self.curr.fetchone()
        if subreddit_qury == None: # create one if one is not found
            print('not found')
            self.curr.execute("""INSERT INTO redditsubreddit
                        (subreddit) VALUES (%s)""", (self.subreddit_name,))

    def save_post_db(self,post_qury, 
                        postTitle, 
                        postUserName, 
                        postUpVotes, 
                        postPercentUpVotes,
                        commentQuanity,
                        postText,
                        postDateTime):
        if post_qury == None: # create one if one is not found
            print('post not found in db attempt to save for first time')   
            if postDateTime < self.post_time_saved:
                self.post_time_saved = postDateTime
                print(self.post_time_saved)
                print('\n')
            self.curr.execute("""INSERT INTO redditpost
                        (title,
                        username,
                        upvotes,
                        percentupvotes,
                        commentquanity,
                        posttext,
                        datetime,
                        subreddit)
                        VALUES (%s , %s, %s, %s, %s, %s, %s, %s )
                        """,
                        (postTitle,
                        postUserName, 
                        postUpVotes, 
                        postPercentUpVotes, 
                        commentQuanity, 
                        postText,
                        postDateTime,
                        self.subreddit_name))
        else: # post is not None update information
            
            if post_qury[7] < self.post_time_saved:
                self.post_time_saved = post_qury[7]
                print(self.post_time_saved)
                print('\n')
            self.curr.execute("""UPDATE redditpost SET
                        title= %s,
                        username= %s,
                        upvotes= %s,
                        percentupvotes= %s,
                        commentquanity= %s,
                        posttext= %s,
                        datetime= %s,
                        subreddit = %s
                        WHERE id=%s
                        """,
                        ( post_qury[1], 
                        post_qury[2], 
                        postUpVotes, 
                        postPercentUpVotes, 
                        commentQuanity, 
                        post_qury[6], 
                        post_qury[7], 
                        self.subreddit_name,
                        post_qury[0]))

    def save_comment_db(self,
                    username,
                    commentUpVotes, 
                    commentTimeSince, 
                    commentText, 
                    postid, ):
        
        
        # check if comment exists
        if username is None or commentUpVotes is None or  commentTimeSince is None or  commentText is None or  postid is None:
            pass
        else:
            print('SAVE COMMENT postid=',postid)
            self.curr.execute("""SELECT id FROM redditcomment
                            WHERE commenttext=(%s)""", (commentText,))
            comment_id = self.curr.fetchone()
            if comment_id == None: # create one if one is not found
                if commentTimeSince < self.comment_time_saved:
                    self.comment_time_saved = commentTimeSince
                    print(self.comment_time_saved)
                self.curr.execute("""INSERT INTO redditcomment
                            (commentusername,
                            upvotes, 
                            datetime, 
                            commenttext, 
                            postid, 
                            subreddit)
                            VALUES (%s , %s, %s, %s, %s, %s)
                            """,
                            (username,
                            commentUpVotes, 
                            commentTimeSince, 
                            commentText, 
                            postid, 
                            self.subreddit_name,))
            else: # comment is not None update information
                if commentTimeSince < self.comment_time_saved:
                    self.comment_time_saved = commentTimeSince
                    print(self.comment_time_saved)

                self.curr.execute("""UPDATE redditcomment SET
                            commentusername= %s,
                            upvotes= %s,
                            datetime= %s,
                            commenttext= %s,
                            postid= %s,
                            subreddit= %s
                            WHERE id=%s
                            """,
                            (username, 
                            commentUpVotes, 
                            commentTimeSince, 
                            commentText,
                            postid,
                            self.subreddit_name,
                            comment_id,))
     
    def combine_paragraphs(self, list_of_paragraphs):
        # print(list_of_paragraphs)
        if len(list_of_paragraphs) == 1:
            return list_of_paragraphs[0]
        else:
            TextOut = ''
            for paragraph in list_of_paragraphs:
                if paragraph !=None:
                    TextOut = ' ' + paragraph
            return TextOut

    def time_since_to_date(self, postTimeSince):
        """
        converts string of how long it been since post and converts to datetime object
        """
        if postTimeSince is not None:
            time_since_words =  postTimeSince.split()
            date = datetime.now()
            if time_since_words[0] == 'just': # just now
                pass
            elif time_since_words[1] == 'hours' or time_since_words[1] =='hour': # 3 hours since
                hour = timedelta(hours=int(time_since_words[0]))
                date = date - hour
            elif time_since_words[1] == 'minutes' or time_since_words[1] == 'minute': # 15 minutes since
                minute = timedelta(minutes=int(time_since_words[0]))
                date = date - minute
            elif time_since_words[1] == 'days' or  time_since_words[1] == 'day': # 15 days since
                days = timedelta(days=int(time_since_words[0]))
                date = date - days
            elif time_since_words[1] == 'months' or time_since_words[1] == 'month': # 2 months since
                months = timedelta(months=int(time_since_words[0]))
                date = date - months
            else:
                print('time_since does not match pattern three examples: just now, 3 hours later, 15 minutes since', postTimeSince)
                print('showing ',time_since_words)
            return date

    def upVotesFormater(self, postUpVotes):
        if postUpVotes == '•' or postUpVotes == 'None' or postUpVotes=='Vote':
            postUpVotes = '0'
        elif postUpVotes[-1] == 'k':
            postUpVotes = float(postUpVotes[:-1]) * 1000
        return int(postUpVotes)

    def postPercentUpVotesFormater(self, postPercentUpVotes):
        # 100% Upvoted
        if postPercentUpVotes:
            postPercentUpVotesWords = postPercentUpVotes.split()
            return int(postPercentUpVotesWords[0][:-1])
        else:
            return 0

    def create_post_comment_last_saved_tables(self):
        self.comment_time_saved = datetime.now()
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditlastcommentupdate (
            datetime timestamp NOT NULL,
            subreddit varchar(30) references redditsubreddit(subreddit) UNIQUE,   
            CONSTRAINT fk_redditsubreddit
                FOREIGN KEY(subreddit)
                    REFERENCES redditsubreddit(subreddit) 
                );""")
        self.post_time_saved = datetime.now()
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditlastpostupdate (
            datetime timestamp NOT NULL,
            subreddit varchar(30) references redditsubreddit(subreddit) UNIQUE,    
            CONSTRAINT fk_redditsubreddit
                FOREIGN KEY(subreddit)
                    REFERENCES redditsubreddit(subreddit) 
                );""")
        


# sample dict of item passed from spider
"""{'postTitle': 'LMT Stock', 'postUserName': 'u/Historical_Peak_696', 'postTimeSince': '3 hours ago', 'postUpVotes': '2', 'postPercentUpVotes': None, 'commentQuanity': '7 comments', 'postText': ['Why is
LMT struggling so much this year?  They seem to have great analyst targets as well as good forecasts from sources like The Street & CFRA.  NOC seems to be following the same trend.  I have been holding the stock for about 2 years and assumed defense would be a good industry to be in during a pandemic because it’s something we can’t go without.  Why are these stocks continuing to slide and what are your thoughts on LMT  long term?'], 'comments': [{'commentUserName': 'Junkbot', 'points': '2 points', 'commentTimeSince': '3 hours ago', 'commentText': ['Most defense tickers are suffering. At least BA
has exposure outside.']}, {'commentUserName': 'natterdog1234', 'points': '2 points', 'commentTimeSince': '3 hours ago', 'commentText': ['It’s a steal rn']}, {'commentUserName': 'wordsforthewind96', 'points': '1 point', 'commentTimeSince': '2 hours ago', 'commentText': ["yep I'm buying at these levels"]}, {'commentUserName': 'Original-Opportunity', 'points': '2 points', 'commentTimeSince': '3 hours ago', 'commentText': ['They operate in cycles.  Personally I like LHX.']}, {'commentUserName': 'ray_kats', 'points': '1 point', 'commentTimeSince': '3 hours ago', 'commentText': ["Fantastic company but
war and conflicts are what's good for defense stocks."]}, {'commentUserName': '7thAccountDontDelete', 'points': '1 point', 'commentTimeSince': '2 hours ago', 'commentText': ['With a 14 PE and decades long contracts with the biggest defense spender in the world, it’s a steal right now. They’ve been increasing their dividends by about 10% a year too.']}, {'commentUserName': 'drjelt', 'points': '1 point', 'commentTimeSince': '2 hours ago', 'commentText': ['Holding it for long term. Adding more if it drops further']}]}"""
