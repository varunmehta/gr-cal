README
========

If you have issues installing the pip's, google it.

 * Added support for different date formats
 * Made the code span across months
 * Batch push introduced, makes the process move a 1000 times faster! 

# HTML Parser
Install Beautiful Soup - http://www.crummy.com/software/BeautifulSoup/

```
 $ pip install beautifulsoup4
```

```
 $ pip install requests
```


## For Mac OS X 
Install the xcode tools before proceeding 

``` 
 $ xcode-select --install 
```

Since we are deploying on the Pi, we need something fast and light, so install lxml as the parser, rather than the default one.

```
 $ pip install lxml
```

# Google Calendar API - Google Client Library
We are pushing the data to google calendar, read more here: https://developers.google.com/google-apps/calendar/quickstart/python 

```
 $ pip install --upgrade google-api-python-client
```
## Public Calendar URL
https://www.google.com/calendar/embed?src=u5djqf0coesftoag7cehe3ampo%40group.calendar.google.com&ctz=America/New_York

  