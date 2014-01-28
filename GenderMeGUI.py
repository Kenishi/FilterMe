import sys, signal, sqlite3, webbrowser
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtWebKit import  *

con = None # SQLite Connection

DEBUG = True
def log(str):
	if DEBUG:
		print str

class GenderMeTable(QTableWidget):	
	USER_ID_COLUMN = 3
	COLUMN_COUNT = 4
	
	def __init__(self,parent):
		super(QTableWidget,self).__init__(parent)
	
	def setWebView(self, wv):
		self.webview = wv

	def sizeHint(self):
		width = 0
		print str(self.columnCount())
		for i in range(self.columnCount()):
			width += self.columnWidth(i)

		width += self.verticalHeader().sizeHint().width()

		width += self.verticalScrollBar().sizeHint().width()
		width += self.frameWidth()*2
		width += 30

		return QSize(width,self.height())		
	
	def openURL(self, row, col):
		new = 2
		url="http://mixi.jp/show_friend.pl?id=" + unicode(self.item(row,3).text())
		webbrowser.open(url,new=new)
		
	def currentChanged(self,current, previous):
		global con
		id = self.item(current.row(),3).text()
		cur = con.cursor()
		cur.execute("""SELECT name, age, sex, location, intro FROM users WHERE user_id=?""", (int(id),))
		(name,age,sex,location,intro) = cur.fetchone()
		
		html = """<html><body>
		<br/>
		<b>Name:</b> %s <br />
		<b>Age:</b> %s <br/>
		<b>Sex:</b> %s <br/>
		<b>Location:</b> %s <br />
		<br/>
		<center><h3>Intro</h3></center><br />
		%s
		</body></html>""" % (name, unicode(age).strip(), unicode(sex), unicode(location).strip(), unicode(intro))
		
		self.webview.page().mainFrame().setHtml(html)
		
		return super(QTableWidget,self).currentChanged(current,previous)


class GenderMeGUI(QMainWindow):
	SQL_DB = "users.sqlite"
	MALE = u'\"男性\"'
	FEMALE = u'\"女性\"'
	NONE = u'\"?\"'
	data_list = QStandardItemModel()
	
	def __init__(self, parent=None):
		global con
		
		super(GenderMeGUI, self).__init__()	
		con = sqlite3.connect(self.SQL_DB)
		self.initUI()
	
	def buildSex(self,s_flags):
		str = " , ".join((s_flags))
		return str		
	
	def search(self, txt=None, sex_flag=(FEMALE,)):
		cur = con.cursor()
		
		if txt == None or txt == "":
			exe = """SELECT name,age,location,user_id FROM users WHERE intro LIKE '%%' AND (sex IN (%s))""" % (self.buildSex(sex_flag),)
		else:
			exe = """SELECT name,age,location,user_id FROM users WHERE intro LIKE '%%%s%%' AND (sex IN (%s)) """ % (unicode(txt),self.buildSex(sex_flag))
			
		cur.execute(exe)
		self.tw.clear()
		self.tw.setHorizontalHeaderLabels(["Name","Age","Location","ID"])
		data = cur.fetchall()
		
		self.tw.setRowCount(len(data))
		row = 0		
		
		"""
		for x in data:			
			y = 0
			for y in range(4):
				item = QStandardItem(unicode(x[y]))
				self.tw.data_list.setItem(row, y, item)
			row += 1
		"""
		for x in data:			
			y = 0
			for y in range(self.tw.COLUMN_COUNT):
				item = QTableWidgetItem(unicode(x[y]))
				self.tw.setItem(row, y, item)
			row += 1

	def signal_doSearch(self):
		flag = []
		txt = self.search_txt.text().__str__().strip()
		if self.check_f.checkState(): flag.append(self.FEMALE)
		if self.check_m.checkState(): flag.append(self.MALE)
		if self.check_n.checkState(): flag.append(self.NONE)		
		self.search(txt,flag)
		

	def initUI(self):
		centralWidget = QWidget()
		
		mainLayout = QHBoxLayout()			# Central widget layout control
		#mainLayout = QGridLayout()			# Central widget layout control
		centralWidget.setLayout(mainLayout)	# Set centralWidget layout
		
		searchLayout = QGridLayout()
		
		## Search Tools
		self.search_txt = txt = QLineEdit()
		searchLayout.addWidget(txt,0,0)
		
		self.check_f = cf = QCheckBox(text=u"女")
		cf.setCheckState(Qt.Checked)
		searchLayout.addWidget(cf,0,1)
		
		self.check_m = cm = QCheckBox(text=u"男")
		searchLayout.addWidget(cm,0,2)
		
		self.check_n = cn = QCheckBox(text=u"無")
		searchLayout.addWidget(cn,0,3)
		
		self.search_btn = btn_s = QPushButton(text="Search")
		searchLayout.addWidget(btn_s,0,4)
		self.connect(btn_s, SIGNAL("pressed()"),self.signal_doSearch)

		## WebPage View
		self.webview = wview = QWebView()
		wview.setSizePolicy(QSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)) # Webview can expand as it needs to
		
		str = "<html><body><center><h3>No user loaded</h3></center></body></html>"
		wview.page().mainFrame().setHtml(str)
		mainLayout.addWidget(wview)

		## SQL Table View
		self.tw = tw = GenderMeTable(centralWidget)	# Create & Add TableWidget too central window
		tw.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,QSizePolicy.MinimumExpanding)) # Table Horizontal size should be Fixed, but vert can expand if need be
		tw.setColumnCount(tw.COLUMN_COUNT)
		tw.setColumnHidden(tw.USER_ID_COLUMN,True)  # ID is in a column because theres no easy way to access from internal list
		tw.setColumnWidth(0,200)
		tw.setColumnWidth(1,70)
		tw.setColumnWidth(2,200)
		tw.setWebView(self.webview)
		tw.setSortingEnabled(True)
		self.connect(tw, SIGNAL("cellDoubleClicked(int,int)"), tw.openURL)
		searchLayout.addWidget(tw,1,0,1,5)
		
		mainLayout.addLayout(searchLayout)
		
		self.setCentralWidget(centralWidget)
		self.setGeometry(50,50,1000,650)	# Set Window's geometry
		self.setWindowTitle('GenderMe')
		self.show()
		self.search()
	
class GenderMeApp():
	def __init__(self):
		self.gui = GenderMeGUI()
	
		### Force UTF-8 encoding across QT ###
		QTextCodec.setCodecForCStrings(QTextCodec.codecForName("utf8"))		
		

def main():
	app = QApplication(sys.argv)
	
	gmeApp = GenderMeApp()
	sys.exit(app.exec_())

if __name__ == '__main__':
	signal.signal(signal.SIGINT, signal.SIG_DFL) ## Allows for CTRL+C breakout of PyQT program
	main()

