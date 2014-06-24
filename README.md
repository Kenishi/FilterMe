# GenderMe
## A small Python tool which tries to gather and filter users in Mixi groups to make it easier to find people with common interests.

###Requirements:
  * Python 2.7x
  * PyQt 4.8

###HOW TO USE:
1. Get a Mixi account
2. Run GenderMe.py first. Login.
3. When asked for group ID, you can find this in the URL for the group, it's the string of numbers after id=
4. Let the script run till complete or till you get tired. Simply close the console screen.
Note: I have left a lot of the debug loggin in so its easy to see whats going on.
5. Run GenderMeGUI.py

The input box will search the Intro text for that text.
The check box Female/Male/None (left to right respectively), allow you to filter for the gender.
Press search to get results from the DB.

Note: You can **NOT** run the Gatherer and search the database at the same time.


LEARNING GOALS: None

PROBLEM: Mixi.jp is a Japanese SNS site much like Facebook. In recent years Facebook has eclipsed the service. One of the nice things about the site though is that it still remains a good place for people of common interests to gather and talk about things they like. Mixi has avoided allowing people to really use the service to find people of similar interests to meet up. As a result, there lacks options such as "Find people that like X and are of gender Y and age Z." This small script attempted to tackle the problem.

SOLUTION: The way I decided to attack the problem was in two parts: Gatherer and Viewer. First I created a Python script which would crawl through a group the user supplied. For example, maybe a group that's focused on a single, popular TV show. Once given the group ID, it would access the group's member list and start harvesting users and visiting the user's profile page. The profile would be parsed and dumped into a SQLiteDB. Most of the user information would be stored. Ideally the parser would run till it hits the end of the list, but because of various issues, its sometimes more optimal to simply close the script after 20-30 minutes, especially if the group is large. It is worth noting that users are saved and that the user info isn't tied to a single group, so its possible that across multiple groups, you might run across the same user again, but the parser would skip it since its already in the DB.

The second part that I created was a simply GUI in Python which would allow the user to specify the gender and a search term. The Viewer script would open up the SQLiteDB and search through the entries. The search term would look through the personal intro that a user wrote and try and match against that. So if you specified "Female" and search term "Sci-fi" it would look for all "female" users that mentioned "sci-fi" in their intro.

The program works still (thankfully), but there still exists problems with flood detection that I haven't been able to work around. I primarily built this small tool as sort of a proof-of-concept that I could make it. But since I don't live in Japan at the moment, the desire to work on it isn't quite there.

Known Issues:
* Flood detection problems - Mixi will temporarily block accessing the site if it detects excessive hits from your IP. Attempts to jitter accesses and add in sleep times have not fixed this issue.

Things To-Do:
* Centralize into a single application so that the scripts are not split
* Clean up code to better match my current standard for written code and layout.
* Clean up the GUI
* Create tests to help discover edge cases in parsing
