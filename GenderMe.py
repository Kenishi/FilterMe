import sys,time,sqlite3,re,threading,random

from requests import session
from bs4 import BeautifulSoup as bsoup

MIXI_URL = "http://mixi.jp/show_friend.pl?id=" # The mixi base url
SQL_DB = "users.sqlite"	# The SQLite data that is used

m_session = None
group_url = "http://mixi.jp/list_member.pl?id="  #Specify the group list_member URL to scan
group_id = None

users = []
isFinished = False
quickExit = False\

JITTER_MIN = 1000	# The jitter min time (ms) between ParseUser executions
JITTER_MAX = 3500	# The jitter max time (ms) between ParseUser executions
SLEEP_INTERVAL = 5	# Sleep every 5 user requests
SLEEP_TIME = 30		# Sleep for 10 seconds after SLEEP_INTERVAL
FLOOD_TIME = (60 * 3)		# Sleep for 3 minutes when a flood is detected

###### TODO: Use "div.messageArea h3" to determine flood or restricted. Restr = アクセスできません Flood = 内容確認 followed by complete page blanking


def isFlood(res):
	soup = bsoup(res.text)
	sel = soup.select(".messageArea h3")
	if sel:
		sel = sel[0].decode_contents()
		if sel == u'内容確認' and u'存在しないユーザIDです' not in res.text:
			return True
		else:
			return False
	else:
		return False

def isRestricted(res):
	soup = bsoup(res.text)
	sel = soup.select(".messageArea h3")
	if sel:
		sel = sel[0].decode_contents()
		if sel == u'アクセスできません':
			return True
		else:
			print "Restricted?: %s" % (sel,)
			return False
	else:
		return False

class ParseUser(threading.Thread):
	def run(self):
		print "Thread started.\n"
		conn = sqlite3.connect(SQL_DB)
		cur = conn.cursor()
		cur.execute('''CREATE TABLE IF NOT EXISTS users  ("user_id" INTEGER NOT NULL  UNIQUE , "name" TEXT, "age" INTEGER, "sex" TEXT NOT NULL , "location" TEXT, "intro" TEXT, "restricted" BOOL DEFAULT 0) ''');
		
		count = 0
		while (not isFinished and not quickExit) or users: # While ParseList is running or we have users in the Pool, run
			if not users:
				print "No users. Sleeping."
				time.sleep(2) # No users in pool yet, sleep for a bit
			else:
				user = users.pop() # Grab a user
				
				## Check if we have scsanned the user
				cur.execute('''SELECT * FROM users WHERE user_id=?''',(int(user),))
				if len(cur.fetchall()):
					print "%s already exists" % (user,)
					continue # User already exists.
				
				print "ParseUser: %s" % (MIXI_URL + user)
				res = m_session.get(MIXI_URL + user) # Grab user page using our auth. session
				soup = bsoup(res.text) # Make soup
				
				## Flood Detect
				if isFlood(res): # Check for flooding
					print "Flood Detected in ParaseUser! Waiting..."
					users.append(user) # Put user back 
					t = FLOOD_TIME
					while(t > 0):
						sys.stdout.write(str(t) + "s ")
						time.sleep(5)
						t = t - 5
					sys.stdout.write("\n")
					continue # Start over
				
				## Check for errors
				if not res.status_code == 200: # Check response for error, just in case
					print "Error (%s): %d" % (user,res.status,)
				elif isRestricted(res) or res.url == "http://mixi.jp/home.pl": # Check for restricted user (ie: underage)
					cur.execute('''INSERT INTO users(user_id,restricted,sex) VALUES (?,?,?)''',(user,True,"Restricted"))
					conn.commit()
				else: # No problems
					user_info = soup.select(".profileListTable tr") # Grab user info section
					import_data = {'sex':'?', 'age':None, 'location':None, 'intro':None, 'name':None} # Prep the user info dict.
					
					#Parse out user info
					for x in user_info:
						if x.th.contents is None:
							sys.exit(1)
						elif x.th.contents[0] == u'性別':
							import_data['sex'] = x.td.decode_contents().strip()
							if import_data['sex'] == u'男性': # Don't need male users
								break
						elif x.th.contents[0] == u'年齢':
							import_data['age'] = x.td.decode_contents()
						elif x.th.contents[0] == u'現住所':
							import_data['location'] = x.td.decode_contents()
						elif x.th.contents[0] == u'自己紹介':
							import_data['intro'] = x.td.decode_contents()
					
					
					## Continue on only if its not a guy
					## Grab the name if sex is F or non-specified
					
					if import_data['sex'] == u'女性' or import_data['sex'] == "?":
						import_data['name'] = soup.title.contents[0].string.strip('[mixi] ')
				
						## Dump to DB now
						cur.execute('''INSERT INTO users(user_id,name,age,sex,location,intro) VALUES(?,?,?,?,?,?)''',(user,import_data['name'],import_data['age'],import_data['sex'],import_data['location'],import_data['intro']))
						conn.commit()
					else:
						cur.execute('''INSERT INTO users(user_id,sex) VALUES(?,?)''', (user,import_data['sex']))
						conn.commit()
				if count < SLEEP_INTERVAL:
					count += 1
					jitter = random.randint(JITTER_MIN,JITTER_MAX) / 1000.0
					print "Jitter " + str(jitter)
					time.sleep(jitter)
				else:
					count = 0
					time.sleep(SLEEP_TIME)
			
		conn.close()	
		print "isFinished: %r users: %d" % (isFinished,len(users))
	
def ParseList():
	global m_session
	global group_url
	global isFinished
	
	if m_session is None or group_url is None:
		print "Session or URL is NULL. Abort."
		sys.exit(1)
		
	page = 1
	
	while(True):
		if len(users) > 100:
			time.sleep(20) # No need to pound the server till we get the user count back down
			
		url = group_url + "&page=" + str(page)
		print "GET " + url
		res = m_session.get(url)
		
		## Check for flood detection
		if isFlood(res):
			sys.stdout.write("Flood Detected. Wait ")
			t = FLOOD_TIME
			while(t > 0):
				sys.stdout.write(str(t) + "s ")
				time.sleep(5)
				t = t - 5
			sys.stdout.write("\n")
			continue
		
		
		soup = bsoup(res.text) ## Make Soup
		list = soup.select(".iconList03 li a") ## Grab user block
		
		## Check for End of Pages
		if not list:
			break # End of Pages, break from loop
		
		## Parse for Users
		for x in list:
			users.append(re.search("(?<=&id\=)[0-9]*", x['href']).group(0))
		page += 1
		time.sleep(5)
	isFinished = True
		
def login():
	global m_session
	
	username = raw_input("Mixi Username: ");
	password = raw_input("Mixi Password: ");
		
	payload = {
		'next_url' : '/home.pl',
		'post_key' : '',
		'email' : username,
		'password' : password,
		'x' : 0,
		'y' : 0
	}
	
	m_session = session()
	
	#Get post_key
	res = m_session.get('http://mixi.jp/')
	soup = bsoup(res.text)
	payload['post_key'] = (soup.find_all('input',attrs={'name':'post_key'})[0])['value']
	
	#Try Logging In
	res = m_session.post('http://mixi.jp/login.pl', data=payload)
	if not "check.pl" in res.text:
		print "Login Failed. Abort."
		sys.exit(1)
	print "Login Complete"

def getGroupID():
	global group_id
	
	group_id = raw_input("Input group id to parse for users (This is the number after ?id= in the group's URL:")

try:
	login()
	getGroupID()
	thread = ParseUser()
	thread.start()
	ParseList()
except KeyboardInterrupt:
	quickExit = True
	sys.exit(1)
