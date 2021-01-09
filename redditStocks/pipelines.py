# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import psycopg2
from datetime import datetime, timedelta 
"""
Post Varibles:
    postTitle
    postUserName
    postTimeSince
    postUpVotes
    postPercentUpVotes
    commentQuanity
    postText
"""
"""
Comment Varibles
    comments = [
        commentUserName 
        points
        commentTimeSince
        commentText
    ]
"""

class RedditstocksPipeline:

    def open_spider(self, spider):
        #connect to database
        self.conn = psycopg2.connect(
                host="34.72.244.217",
                database="postgres", 
                user="postgres", 
                password="tKJ6uSBpwvMy")
        self.conn.autocommit=True

        self.curr = self.conn.cursor()
        #create table for post
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditpost (
                id serial,
                title varchar(255) NOT NULL,
                username varchar(255) NOT NULL,
                upvotes int NOT NULL,
                percentupvotes int NOT NULL,
                commentquanity int NOT NULL,
                posttext varchar(3000), 
                datetime timestamp NOT NULL,
                PRIMARY KEY(id)
            );""")        
        # create table for comments
        self.curr.execute("""CREATE TABLE IF NOT EXISTS redditcomment (
                postid int references redditpost(id),
                commentusername varchar(255) NOT NULL,
                points int,
                commenttext varchar(3000),
                datetime timestamp NOT NULL,
                CONSTRAINT fk_redditpost
                    FOREIGN KEY(postid) 
                        REFERENCES redditpost(id)
            );""")    
        pass

    def process_item(self, item, spider):
        postTitle = item['postTitle']
        postUserName = item['postUserName']
        postText = item['postText']
        postTimeSince = item['postTimeSince']
        postUpVotes = item['postUpVotes']
        postPercentUpVotes = item['postPercentUpVotes']
        commentQuanity = len(item['comments'])
      
        # commbine postText paragraphs into one string
        postText = self.combine_paragraphs(postText)
        # create time stamp
        postDateTime = self.time_since_to_date(postTimeSince)
        #format the post votes to int
        postUpVotes = self.upVotesFormater(postUpVotes)
        postPercentUpVotes = self.postPercentUpVotesFormater(postPercentUpVotes)

        post = self.curr.execute("""SELECT * FROM redditpost;""")
        print(type(post))
        print('zzzzzzzzzzzzz', post)
        if post is None:
            # save post information
            self.curr.execute("""insert into redditpost
                (title, username, upvotes, percentupvotes, commentquanity, posttext , datetime)
                VALUES (%s,%s,%s,%s,%s,%s,%s);""",
            (postTitle, postUserName, postUpVotes, postPercentUpVotes, commentQuanity, postText, postDateTime )
            )
        else:
            self.curr.execute(
                """UPDATE redditpost SET (upvotes, percentupvotes, commentquanity,postdatetime)
                VALUES (%s,%s,%s,%s)
                WHERE title LIKE %s;""",
                (postUpVotes,postPercentUpVotes,commentQuanity,postDateTime, postTitle)
                )

        if commentQuanity == 0:
            pass
        else:
            self.curr.execute("""SELECT id FROM redditpost WHERE title=%s ;""", (str(postTitle),))
            postId = self.curr.fetchone()
            print(postId, ' jjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj')
            for comment in item['comments']:
                commentUserName = comment['commentUserName'] 
                commentPoints = comment['points']
                commentTimeSince = comment['commentTimeSince'] 
                commentText = comment['commentText'] 
                if commentUserName == None or commentPoints == None or commentTimeSince ==None or commentText ==None:
                    commentQuanity = commentQuanity -1
                    pass
                else:
                    # commbine postText paragraphs into one string
                    commentText = self.combine_paragraphs(commentText)
                    # create time stamp
                    commentDateTime = self.time_since_to_date(commentTimeSince)
                    #format the post votes to int
                    commentPoints = self.commentPointsFormatter(commentPoints)
                    print(commentUserName,commentPoints,commentDateTime, commentText  )

                    com = self.curr.execute("""SELECT * FROM redditcomment WHERE commenttext=%s ;""", (str(commentText),))
                    if com is None:
                        # save post information
                        self.curr.execute("""insert into redditcomment
                            (postid, commentusername, points, commenttext, datetime)
                            VALUES (%s,%s,%s,%s,%s);""",
                        (postId, commentUserName, commentPoints, commentText, commentDateTime)
                        )
          
                # self.curr.execute(
                #     """UPDATE redditcomment SET (postid, upvotes, percentupvotes, commentquanity, postdatetime)
                #     VALUES (%s,%s,%s,%s,%s)
                #     WHERE id=%s;""",
                #     (postId, postUpVotes, postPercentUpVotes, commentQuanity, postDateTime, postId)
                #     )
        return item



    def close_spider(self, spider):
        self.conn.close()
        self.curr.close()

    def combine_paragraphs(self, list_of_paragraphs):
        print(list_of_paragraphs)
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
        time_since_words =  postTimeSince.split()
        date = datetime.now()
        if time_since_words[0] == 'just': # just now
            pass
        elif time_since_words[1] == 'hours': # 3 hours since
            hour = timedelta(hours=int(time_since_words[0]))
            date = date - hour
        elif time_since_words[1] == 'minutes': # 15 minutes since
            minute = timedelta(minutes=int(time_since_words[0]))
            date = date - minute
        else:
            print('time_since does not match pattern: just now, 3 hours later, 15 minutes since', postTimeSince)
        return date
    
    def upVotesFormater(self, postUpVotes):
        if postUpVotes == '•':
            postUpVotes = '0'
        return int(postUpVotes)
    
    def postPercentUpVotesFormater(self, postPercentUpVotes):
        # 100% Upvoted
        postPercentUpVotesWords = postPercentUpVotes.split()
        return int(postPercentUpVotesWords[0][:-1])
    
    def commentPointsFormatter(self, commentPoints):
        comment_points_words = commentPoints.split()
        if comment_points_words[1] == 'hidden':
            return None
        else:
            return int(comment_points_words[0])

        

# sample Jason of item passed from spider
"""{'postTitle': 'LMT Stock', 'postUserName': 'u/Historical_Peak_696', 'postTimeSince': '3 hours ago', 'postUpVotes': '2', 'postPercentUpVotes': None, 'commentQuanity': '7 comments', 'postText': ['Why is 
LMT struggling so much this year?  They seem to have great analyst targets as well as good forecasts from sources like The Street & CFRA.  NOC seems to be following the same trend.  I have been holding the stock for about 2 years and assumed defense would be a good industry to be in during a pandemic because it’s something we can’t go without.  Why are these stocks continuing to slide and what are your thoughts on LMT  long term?'], 'comments': [{'commentUserName': 'Junkbot', 'points': '2 points', 'commentTimeSince': '3 hours ago', 'commentText': ['Most defense tickers are suffering. At least BA 
has exposure outside.']}, {'commentUserName': 'natterdog1234', 'points': '2 points', 'commentTimeSince': '3 hours ago', 'commentText': ['It’s a steal rn']}, {'commentUserName': 'wordsforthewind96', 'points': '1 point', 'commentTimeSince': '2 hours ago', 'commentText': ["yep I'm buying at these levels"]}, {'commentUserName': 'Original-Opportunity', 'points': '2 points', 'commentTimeSince': '3 hours ago', 'commentText': ['They operate in cycles.  Personally I like LHX.']}, {'commentUserName': 'ray_kats', 'points': '1 point', 'commentTimeSince': '3 hours ago', 'commentText': ["Fantastic company but 
war and conflicts are what's good for defense stocks."]}, {'commentUserName': '7thAccountDontDelete', 'points': '1 point', 'commentTimeSince': '2 hours ago', 'commentText': ['With a 14 PE and decades long contracts with the biggest defense spender in the world, it’s a steal right now. They’ve been increasing their dividends by about 10% a year too.']}, {'commentUserName': 'drjelt', 'points': '1 point', 'commentTimeSince': '2 hours ago', 'commentText': ['Holding it for long term. Adding more if it drops further']}]}"""