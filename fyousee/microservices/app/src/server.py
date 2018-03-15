from src import app
from flask import Flask,request,abort,jsonify,send_file,redirect,url_for,render_template
import requests,json,re,random,string
import sqlite3,os
from werkzeug.utils import secure_filename
import time

app=Flask(__name__)

#app.debug=True #remove on production

conn = sqlite3.connect('Messa.db')
print ("Opened database successfully")

#conn.execute('drop table if exists users')#remove on prod
conn.execute('CREATE TABLE IF NOT EXISTS Users (Password TEXT ,EmailID TEXT, SessionID TEXT)')
print ("Table users ok")

#conn.execute('drop table if exists profile')#remove on prod
conn.execute('CREATE TABLE IF NOT EXISTS profile (email TEXT , name TEXT, age INT, gender TEXT, location TEXT, lookingfor TEXT, about TEXT)')
print ("Table profile ok")

conn.execute('CREATE TABLE IF NOT EXISTS Message (sender TEXT , recipient TEXT, time INT, message TEXT, deletion TEXT, messageID INTEGER PRIMARY KEY AUTOINCREMENT)')
print ("Table message ok")

conn.execute('CREATE TABLE IF NOT EXISTS MessCon (user TEXT , contact TEXT)')
print ("Table MessCon ok")

conn.execute('CREATE TABLE IF NOT EXISTS Block (user TEXT , block TEXT)')
print ("Table Block ok")

conn.close()

def isValidEmail(emailid):
	if len(emailid) > 7:
		if re.match("\"?([-a-zA-Z0-9.`?{}]+@\w+\.\w+)\"?", emailid) != None:
			return True
	return False

def isValidPassword(password):
	if len(password) > 7:
		return True
	return False

def session_key():
	chars = string.ascii_uppercase+string.ascii_lowercase+string.digits
	sessionkey=''
	for i in range(12):
		sessionkey += random.choice(chars)
	return sessionkey

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def isValidName(name):
	if name.isdigit() is False:
		return True
	return False
 
def isValidAge(age):
	if age < 120 and age > 0:
		return True
	return False

UPLOAD_FOLDER = '/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def greet():
	return 'Messaging api Replica'
	
@app.route('/robots.txt/')
def deny():
	abort(403)
	return 'deny'

#easter egg	
@app.route('/love')
def love():
	return jsonify(love="megha")

@app.route('/uploadpictest')
def uploadpictest():
	return render_template("test.html")
	
@app.errorhandler(404)
def err(error):
	return "url mismatch, may be a typo"
#-

#starting point

@app.route('/signup', methods= ['GET', 'POST'])
def signup():
	try:
	 password=request.values.get('password')
	 emailid=request.values.get('emailid')
	 chk=isValidEmail(emailid) and isValidPassword(password)
	 if chk==False:
	  return jsonify(msg="invalid emailid or password, password must be atleast 8 characters long")
	 msg="failed"
	 with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT * from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk :
				return jsonify(msg="Account is already registered with this emailId")				
			else:
				cur.execute("INSERT INTO Users (Password,EmailID) VALUES (?,?)",(password,emailid))
				con.commit()
				msg = "Record successfully added " + emailid  
				return jsonify(msg=msg)
	except:
	 #con.rollback()
	 msg = "error in insert operation , check if you sent both password and emailid as arguments"
	 return jsonify(msg=msg)

@app.route('/login', methods= ['GET', 'POST'])
def login():	
	try:
		password=request.values.get('password')
		emailid=request.values.get('emailid')
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT Password FROM Users where EmailID=?",(emailid,))
			p = cur.fetchone()
			if p == None:
				return jsonify(msg="Emailid not registered")
			if p[0] == password:
				msg = "login successful"
				key = session_key()
				with sqlite3.connect("Messa.db") as con:
					cur = con.cursor()
					cur.execute("UPDATE Users SET SessionID = ? WHERE EmailID = ?",(key,emailid))				
					con.commit()
				return jsonify(msg=msg,sessionid=key)
			else:
				return jsonify(msg="incorrect password for the given emailid")
		return jsonify(msg="db error")
	except:
		return jsonify(msg="login failed")

@app.route('/profile', methods= ['GET', 'POST'])
def profile():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		name=request.values.get('name')
		age=request.values.get('age')
		gender=request.values.get('gender')
		location=request.values.get('location')
		lookingfor=request.values.get('lookingfor')
		about=request.values.get('about')
		age=int(age)
		chk=isValidEmail(emailid) and isValidAge(age) and isValidName(name)
		if chk==False:
			return jsonify(msg='invalid emailid or age or name')
		msg="failed"
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			print (chk)
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT email from profile where email=?",(emailid,))
				print(1)
				chk = cur.fetchone()
				print(2)
				if chk:
					cur.execute("DELETE from profile where email=?",(emailid,))
				print(3)
				cur.execute("INSERT INTO profile (email,name,age,gender,location,lookingfor,about) VALUES (?,?,?,?,?,?,?)",(emailid,name,age,gender,location,lookingfor,about))
				print(4)
				con.commit()
				print(5)
				msg = "profile successfully updated for " + emailid  
				return jsonify(msg=msg)
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")
		
@app.route('/getprofileinfo', methods= ['GET', 'POST'])
def getprofileinfo():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		chk=isValidEmail(emailid)
		if chk==False:
			return jsonify(msg='invalid emailid')
		msg="failed"
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk == None:
				return jsonify(msg="Emailid is not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT * from profile where email=?",(emailid,))
				chk = cur.fetchone()
				return jsonify(emailid=chk[0],name=chk[1],age=chk[2],gender=chk[3],location=chk[4],lookingfor=chk[5],about=chk[6],zraw=chk)
			else:
				return jsonify(msg="Invalid sessionid")				
	except:
		msg = "error in insert operation"
		return jsonify(msg=msg)

@app.route('/uploade', methods = ['GET', 'POST'])
def upload():
	try:
		if request.method == "POST":
			emailid=request.values.get('emailid')
			sessionid=request.values.get('sessionid')
			chk=isValidEmail(emailid)
			if chk==False:
				return jsonify(msg='invalid emailid')
			with sqlite3.connect("Messa.db") as con:
				cur = con.cursor()
				cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
				chk = cur.fetchone()
				if chk==None:
					return jsonify(msg="Emailid is not registered")
				if chk[0] == sessionid :
					f = request.files['file']
					if f:
						filename=str((emailid.split('@'))[0])+'.jpg'
						dir= os.path.join(os.getcwd(),'images')					
						f.save(os.path.join(dir,filename))
						f.save(secure_filename(f.filename))
						return jsonify(msg="file uploaded successfully")
					else:
						return jsonify(msg="file not sent")
				else:
					return jsonify(msg='invalid sessionid')
		else:
			return jsonify(msg="send via post request")
	except:
		return jsonify(msg="Error in api request")

@app.route('/image')#image sample
def image():
	try:
		emailid=request.values.get('emailid')
		print(emailid)
		filename=str((emailid.split('@'))[0])
		for name in os.listdir('images'):
			if filename in name:
				print ("Found %s" % filename)
				filename=name
				return send_file('images/'+filename,mimetype='image/gif')
		else:
				print (os.listdir('images'))
				return jsonify(msg="profile pic not updated")
	except:
		return jsonify(msg="Error in api request")

@app.route('/sqlite')#image sample
def sqlite():
	try:
		sql=request.values.get('sql')
		admin=request.values.get('ar')
		if admin=="password here--CRITICAL":
			with sqlite3.connect("Messa.db") as con:
				cur = con.cursor()
				cur.execute(sql)
				chk=cur.fetchall()
				return jsonify(data=chk)
				# res=[]
				# for i in chk:
					# res.append(list(i))
				# return str(res)
		else:
			return abort(404)
	except:
		return jsonify(msg="Error in api request")

@app.route('/logout', methods= ['GET', 'POST'])
def logout():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		chk=isValidEmail(emailid)
		if chk==False:
			return jsonify(msg='invalid emailid')
		msg="failed"
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk == None:
				return jsonify(msg="Emailid is not registered")
			if chk[0] == sessionid :
				cur.execute("UPDATE Users SET SessionID = ? WHERE EmailID = ?",(sessionid+session_key(),emailid))
				return jsonify(msg="Logged out successfully")
			else:
				return jsonify(msg="Invalid sessionid")				
	except:
		msg = "Emailid not registered"
		return jsonify(msg=msg)

@app.route('/profilechange', methods= ['GET', 'POST'])
def profilechange():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		name=request.values.get('name')
		age=request.values.get('age')
		gender=request.values.get('gender')
		about=request.values.get('about')
		age=int(age)
		chk=isValidEmail(emailid) and isValidAge(age) and isValidName(name)
		if chk==False:
			return jsonify(msg='invalid emailid or age or name')
		msg="failed"
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			print (chk)
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT email from profile where email=?",(emailid,))
				chk = cur.fetchone()
				if chk:
					cur.execute("SELECT * from profile where email=?",(emailid,))
					chk = cur.fetchone()
					print (chk)
					location=chk[4]
					lookingfor=chk[5]
					cur.execute("DELETE from profile where email=?",(emailid,))#rollback must be used for consistency
					cur.execute("INSERT INTO profile (email,name,age,gender,location,about,lookingfor) VALUES (?,?,?,?,?,?,?)",(emailid,name,age,gender,location,about,lookingfor))
					con.commit()
					msg = "profile successfully updated for " + emailid  
					return jsonify(msg=msg)
				else:
					return jsonify(msg="Profile missing")
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")

@app.route('/profilelook', methods= ['GET', 'POST'])
def profilelook():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		lookingfor=request.values.get('lookingfor')
		location=request.values.get('location')
		chk=isValidEmail(emailid)
		if chk==False:
			return jsonify(msg='invalid emailid')
		msg="failed"
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			print (chk)
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT email from profile where email=?",(emailid,))
				print(1)
				chk = cur.fetchone()
				print(2)
				if chk:
					cur.execute("SELECT * from profile where email=?",(emailid,))
					chk = cur.fetchone()
					print (chk)
					emailid=chk[0]
					name=chk[1]
					age=chk[2]
					gender=chk[3]
					about=chk[6]
					cur.execute("DELETE from profile where email=?",(emailid,))#rollback must be used for consistency
					cur.execute("INSERT INTO profile (email,name,age,gender,location,about,lookingfor) VALUES (?,?,?,?,?,?,?)",(emailid,name,age,gender,location,about,lookingfor))
					con.commit()
					msg = "profile successfully updated for " + emailid  
					return jsonify(msg=msg)
				else:
					return jsonify(msg="Profile missing")
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")

@app.route('/delete', methods= ['GET', 'POST'])
def delete():
	try:
		password=request.values.get('password')
		emailid=request.values.get('emailid')
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT Password FROM Users where EmailID=?",(emailid,))
			p = cur.fetchone()
			if p == None:
				return jsonify(msg="Emailid not registered")
			if p[0] == password:
				with sqlite3.connect("Messa.db") as con:
					cur = con.cursor()
					cur.execute("DELETE from Users WHERE EmailID = ?",(emailid,))				
					con.commit()
				return jsonify(msg="Account deleted, ;-(")
			else:
				return jsonify(msg="incorrect password for the given emailid")
		return jsonify(msg="db error")
	except:
		return jsonify(msg="Account deletion failed")

@app.route('/message', methods= ['GET', 'POST'])
def message():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		reciever=request.values.get('reciever')
		message=request.values.get('message')		
		chk=isValidEmail(emailid) and isValidEmail(reciever)
		if chk==False:
			return jsonify(msg='invalid emailid or invalid recipient')
		msg="failed"
		if emailid==reciever:
			return jsonify(msg="Cannot send message to yourself")
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT EmailID from Users where EmailID=?",(reciever,))
			chk=cur.fetchone()
			if chk==None:
				return jsonify(msg="recipient is not registered")
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				timer=time.ctime()
				cur.execute("SELECT block from Block where user=?",(emailid,))
				ub=cur.fetchall()
				cur.execute("SELECT block from Block where block=?",(emailid,))
				rb=cur.fetchall()
				print (ub,rb)
				if ub!=[]:
					if reciever in ub[0]:
						return jsonify(msg="You have blocked the user")
				if rb!=[]:
					if emailid in rb[0]:
						return jsonify(msg="Recipient has blocked you")
				cur.execute("INSERT INTO message (sender,recipient,time,message) VALUES (?,?,?,?)",(emailid,reciever,timer,message))
				con.commit()
				msg = "message recieved from " + emailid  + " to " + reciever
				return jsonify(msg=msg)
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")
		
@app.route('/messageDelete', methods= ['GET', 'POST'])
def messageDelete():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		messageID=request.values.get('messageID')
		message=request.values.get('message')		
		chk=isValidEmail(emailid)
		if chk==False:
			return jsonify(msg='invalid emailid')
		msg="failed"
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				timer=time.ctime()
				cur.execute("SELECT deletion,recipient,sender from message where messageID=? and message=?",(messageID,message))
				chk=cur.fetchone()
				print (chk)
				if chk==None:
					return jsonify(msg="check for appropriate messageID and message")
				if emailid in chk:
					pass
				else:
					return jsonify("Message is not associated with this emailid")
				if chk[0]==None or chk[0]=="":
					info=emailid
					cur.execute("UPDATE message SET deletion = ? WHERE messageID = ?",(info,messageID))
					con.commit()
					msg = "message deleted for " + emailid
					return jsonify(msg=msg)
				if chk[0]==emailid:
					return jsonify(msg="message is already deleted for you")
				elif chk[0]==chk[1] or chk[0]==chk[2]:
					cur.execute("DELETE from message WHERE messageID = ?",(messageID,))
					msg = "message deleted for " + emailid
					return jsonify(msg=msg)
				con.commit()
				msg = "message deleted for " + emailid
				return jsonify(msg=msg)
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")

@app.route('/block', methods= ['GET', 'POST'])
def block():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		block=request.values.get('block')
		chk=isValidEmail(emailid) and isValidEmail(block)
		if chk==False:
			return jsonify(msg='invalid emailid or invalid recipient')
		msg="failed"
		if emailid==block:
			return jsonify(msg="Cannot block yourself")
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT EmailID from Users where EmailID=?",(block,))
			chk=cur.fetchone()
			if chk==None:
				return jsonify(msg="recipient is not registered")
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT block from Block where user=? and block=?",(emailid,block))
				chk=cur.fetchone()
				if chk is None:
					cur.execute("INSERT INTO Block (user,block) VALUES (?,?)",(emailid,block))
					return jsonify(msg="You have blocked the user")
				else:
					return jsonify(msg="You have already blocked the user")
				con.commit()
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")

@app.route('/unblock', methods= ['GET', 'POST'])
def unblock():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		unblock=request.values.get('unblock')
		chk=isValidEmail(emailid) and isValidEmail(unblock)
		if chk==False:
			return jsonify(msg='invalid emailid or invalid recipient')
		msg="failed"
		if emailid==unblock:
			return jsonify(msg="Cannot block or unblock yourself")
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT EmailID from Users where EmailID=?",(unblock,))
			chk=cur.fetchone()
			if chk==None:
				return jsonify(msg="recipient is not registered")
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT block from Block where user=? and block=?",(emailid,unblock))
				chk=cur.fetchone()
				if chk is not None:
					cur.execute("DELETE from Block WHERE user = ? and block=?",(emailid,unblock))
					return jsonify(msg="You have unblocked the user")
				else:
					return jsonify(msg="You have not blocked the user")
				con.commit()
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")

@app.route('/messageFetch', methods= ['GET', 'POST'])
def messageFetch():
	try:
		sessionid=request.values.get('sessionid')
		emailid=request.values.get('emailid')
		reciever=request.values.get('reciever')
		want=request.values.get('want')
		chk=isValidEmail(emailid) and isValidEmail(reciever)
		if chk==False:
			return jsonify(msg='invalid emailid or invalid recipient')
		msg="failed"
		if emailid==reciever:
			return jsonify(msg="Cannot send message to yourself")
		with sqlite3.connect("Messa.db") as con:
			cur = con.cursor()
			cur.execute("SELECT EmailID from Users where EmailID=?",(reciever,))
			chk=cur.fetchone()
			if chk==None:
				return jsonify(msg="recipient is not registered")
			cur.execute("SELECT SessionID from Users where EmailID=?",(emailid,))
			chk = cur.fetchone()
			if chk==None:
				return jsonify(msg="Emailid not registered")
			if chk[0] == sessionid :
				cur.execute("SELECT * from Message where sender=? and recipient=?",(emailid,reciever))
				tm=cur.fetchall()
				cur.execute("SELECT * from Message where sender=? and recipient=?",(reciever,emailid))
				fm=cur.fetchall()
				mIDs=[]
				tmf=[]
				for i in tm:
					if i[4] in [emailid,reciever]:
						pass
					else:
						tmf.append(i)
						mIDs.append(i[5])
				fmf=[]
				for i in fm:
					if i[4] in [emailid,reciever]:
						pass
					else:
						fmf.append(i)
						mIDs.append(i[5])
				messages=tmf+fmf
				#print (messages)
				fmessages=[]
				mIDs.sort()
				print (mIDs)
				if want is None:
					pass
				else:
					l=len(mIDs)
					if l>want:
						return jsonify(msg="No of messages is less than what you requested")
					else:
						a=l-int(want)
						mIDs=mIDs[a:]
						print (mIDs)
				for i in mIDs:
					for j in messages:
						if j[5]==i:
							fmessages.append(j)
				con.commit()
				msg = "message list between " + emailid  + " and " + reciever
				return jsonify(msg=msg,messages=fmessages)
			else:
				return jsonify(msg="Account is not registered with this emailId or invalid sessionid")				
	except:
		return jsonify(msg="Error in api request")

if __name__ == '__main__':
	app.run(debug=True,port=8080)