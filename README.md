# Archive-Tweets

This is a command-line tool written in Python 2.7, 
to archive or delete all tweets that you have posted, or that you have liked. 
It is optionally possible to also archive all attached media (images, etc.)

## Use

Windows: set up a UNIX-compatible interface, like Cygwin. Then follow
the Linux/OSX instructions below.

Linux/OSX: Open your terminal, clone this repo, `pip install requirements.txt`.
This software will need to authenticate with Twitter, so you'll need to 
[create an app on Twitter](https://apps.twitter.com/) and insert the credentials obtained
into the `credentials.txt` file.

Then you can run the script. I suggest using `-W ignore` to suppress SSL warnings.
There are several flags:

- `--posted` to indicate that you want to select the tweets you have personally made/retweeted
- `--liked` to indicate that you want to select the tweets you have liked
- `--archive` to indicate that you want to download the selected tweets
- `--delete` to indicate that you want to delete the selected tweets (un-like in the case of `--liked`)
- `--media` to indicate that if you're archiving tweets, you also want to save their media attachments (images, etc.)

You may select only one of `--posted` and `--liked` at a time, not both. The `--media`
flag requires the `--archive` flag: you can only archive the media attachments if you're already
archiving the tweets in the first place.

Some examples of correct use:

`$ python -W ignore TwitterTool.py --archive --media --liked`    
`$ python -W ignore TwitterTool.py --archive --delete --posted`

The software then creates a folder, `Archive-Liked-Tweets` or `Archive-Personal-Tweets`,
depending on whether you selected `--liked` or `--posted`, respectively, and within that,
creates a new folder for every tweet, with the path name given by the timestamp of the tweet's 
publication and the tweet's unique identifier. Within every tweet's folder is the pretty-printed `.json` 
object representing the tweet, as well as any attached media files, if the option to download them was selected.

## Rate Limits

Since this software is reliant on the Twitter API, the rate limits apply:

- For personal tweets, you can make 
[900 queries every 15 minutes](https://dev.twitter.com/rest/reference/get/statuses/user_timeline), 
in blocks of 200 requests per query. 

- For liked tweets, you can make 
[75 queries every 15 minutes](https://dev.twitter.com/rest/reference/get/favorites/list), 
in blocks of 200 requests per query. 

With these generous limits in place, you should find it possible to handle your entire
timeline rather swiftly. Should you hit a rate limit, the app will simply sleep until
the fifteen minute period is over.

## Display

Display of tweets has not been a priority in development so far. I believe there are other
Open-Source projects that have done [a reasonable job](https://github.com/amwhalen/archive-my-tweets) at this, which you can
adapt straight-forwardly. (I'd be happy to accept a PR that generates pages rendering the archived tweets. It is my plan to do this eventually.)

To search all the tweets in a directory for some text, `cd` into the relevant directory, and then use:
`grep -rnw . -e "<your text here>"`
e.g. `grep -rnw ./Archive-Liked-Tweets -e "rice pudding"`

## Notes

- The tool relies on the [Python-Twitter](https://github.com/bear/python-twitter) library,
which provides a helpful wrapper around Twitter's API. Duly note that Twitter makes changes
to their API once in a while (months/years), which makes it possible for the objects 
that the API functions (`api.GetUserTimeline, api.GetFavorites`, etc.) return to be erroneous.

To avoid such errors, you should run this tool from the REPL and make a few calls to the API,
and double-check the JSON objects that you get against the [Twitter API](https://dev.twitter.com/rest/reference).
The documentation for every endpoint has examples of the returned objects.

Example of REPL use:
```
>>> from TwitterTool import *
>>> api = credentials_and_authenticate()
>>> api.GetStatus(824666495305162752).__dict__['_json']                             
>>> api.GetUserTimeline(count=1)
```

- One frequent Twitter pattern is the posting of threads or tweetstorms, which this software
currently does not handle automatically. You'd have to `like` all the tweets in a tweetstorm
to archive all of them. It would be more convenient if you could just `like` the first one,
and the software also grabs the rest for you. This is a bit of an inconvenience. and it's
a currently open issue.
