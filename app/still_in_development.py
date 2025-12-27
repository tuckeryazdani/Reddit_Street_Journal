#Reply Function (Still in development)
# def reminder(desiredSubreddit : str):
#     subreddit = reddit.subreddit(desiredSubreddit)
#     for submission in subreddit.hot(limit=30):
#         for comment in submission.comments:
#             if hasattr(comment,"body"):
#                 lowerComment = comment.body.lower()
#                 if "!remindmebot" in lowerComment:
#                     print(comment.body)
#                     comment.reply("Test is active")

# Subreddit Stats (Still in development)
# def subredditStats(desiredSubreddit):
#     posts=[]
#     comments=[]
#     tests=[]
#     subreddit = reddit.subreddit(desiredSubreddit)
#     for post in subreddit.hot(limit=10):
#         if post.stickied:
#             continue
#         posts.append(post)
#         for comment in post.comments:
#             if hasattr(comment,"body"):
#                 lowerComment=comment.body.lower()
#                 comments.append(post.title)
#                 comments.append(lowerComment)
#     for i in range(0,len(comments),2):
#         tests.append(comments[i]+'\n'+comments[i+1])
#     for i in range(0,len(posts)):
#         posts.insert(i+1,comments.count(posts[i]))

    # ticker_url = f'https://data.nasdaq.com/api/v3/datasets/WIKI/{ticker}.csv'

    # with requests.Session() as s:
    #     response = s.get(ticker_url,headers={'Accept': 'application/json'})
    #     response = response.content.decode('utf-8')
    # response = json.loads(response)
    # if "quandl_error" in response:
    #     raise Exception(response['quandl_error']['code'] + ': ' + response['quandl_error']['message'])

# This was an interesting way to the get the tweet by printing it out in the wsb.py module and grabbing that stdout
# from the terminal
# text = subprocess.Popen(['python',SCRIPT_PATH],stdout=subprocess.PIPE).stdout
# tweet = str(text.read(),'latin-1')