from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt #password u gizlemek için değil parola yerine Esdfarte5565131 gibi gizlemek için.
from functools import wraps


app = Flask(__name__)

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "your username"
app.config["MYSQL_PASSWORD"] = "your password"
app.config["MYSQL_DB"] = "yout blog name"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
app.secret_key = "odeblog" #flash mesajları çalışması için önemsiz bir key.

class RegisterForm(Form):
    name = StringField("Ad-Soyad :",validators=[validators.length(5,50),validators.DataRequired("Ad-Soyad boş geçilemez.")])
    username = StringField("Kullanıcı Adı :",validators=[validators.length(5,50),validators.DataRequired("Kullanıcı Adı boş geçilemez.")])
    email = StringField("Email :",validators = [validators.DataRequired("Email Boş Geçilemez")])
    password = PasswordField("Parola :",validators=[
        validators.DataRequired("Lütfen Parola Girin")
        ,validators.EqualTo(fieldname="confirm",message="Parola Uyuşmuyor..")])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    username = StringField("Lütfen Kullanıcı Adınızı Giriniz")
    password = PasswordField("Lütfen Parolanızı Giriniz")

class ArticleForm(Form):
    title = StringField("Title Of the Aricle",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Contenf Of the Article", validators=[validators.Length(min=10)])


#kayıt olma
@app.route("/register",methods = ["GET","POST"])
def register_page():
    form = RegisterForm(request.form)
    #eğer methodumuz post method ve formumuz valide değilse çalışmaz.
    #valide değilse: mesela yukarıda belirlediğimiz 5-50 karakter dışında isim girilmişse..
    if request.method == "POST"  and form.validate():
        
        #formdaki verileri almak
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        #veritabanında işlem yapabilmek için cursor tanımlamak
        cursor = mysql.connection.cursor()

        #sorgu oluşturmak
        sorgu = "Insert into users (name,email,username,password) VALUES(%s,%s,%s,%s)"
        #sorguyu çalıştırmak ve %s leri aşağıdaki demet ile eşleştirmek
        cursor.execute(sorgu, (name,email,username,password))
        #yaptığımız verileri mysqle işlemek
        mysql.connection.commit()
        #ve işlemi kapatmak
        cursor.close()

        flash("Başarı ile kayıt oldunuz.","success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)

#login işlemi
@app.route("/login", methods = ['GET','POST'])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * from users where username = %s"
        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone() #databasedeki bütün bilgileri al
            real_password = data["password"]#kullanıcının gerçek parolasını al

            if sha256_crypt.verify(password_entered,real_password): #fonksiyon yardımıyla eşit mi diye sorgula
                
                #session(oturum) başlatma işlemi
                session["logged_in"] = True
                session["username"] = username
                
                flash("Başarı ile giriş yaptınız..","success")
                return redirect(url_for("index"))
            else:
                flash("Lütfen Parolanızı Kontrol Edin..","danger")
                return redirect(url_for("login"))
        else:
            flash("Lütfen Doğru Bir Kullanıcı Adı Girin","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html", form=form)


#logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Sadece giriş yapıldığında kontrol panelinin açılması için bir decorator.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args,**kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapın..","danger")
            return redirect(url_for("login"))
    return decorated_function  




@app.route("/dashboard")
@login_required
def dashboard():

    cursor = mysql.connection.cursor()
    sorgu  = "Select * from articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")



    
#makale ekleme
@app.route("/addarticle", methods = ['GET','POST'])
def add_article():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("The article created succesfully","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form)


#makale görüntüleme
@app.route("/article/<string:id>")
def show_article(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("show_article.html",article=article)
    else:
        return render_template("show_articles.html")

#makale silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu, (session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu makaleyi silemezsiniz..", "danger")
        return redirect(url_for("index"))


#makale güncelleme
@app.route("/edit/<string:id>", methods = ['GET','POST'])
@login_required
def update_article(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya böyle bir işlem yapılamaz","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html", form=form)
    else:
        #post request
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles set title = %s,content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale başarıyla güncellendi","success")
        return redirect(url_for("dashboard"))   


@app.route("/")
def index():
    books = ["Akıllı Yatırımcı","Beyin","Yapay Zeka","Şifre Kitabı"]
    return render_template("index.html", answer= "Evet",books=books)

@app.route("/about")
def about_me():
    return render_template("about.html")

@app.route("/articles/<string:id>")
def details(id):
    return "Article Id is :" + id
#article sayfası
@app.route("/articles")
def articles_page():
    cursor=mysql.connection.cursor()
    sorgu = "select * from articles"    
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("article.html",articles=articles)
    else:
        return render_template("article.html")

#url arama
@app.route("/search", methods = ['GET','POST']) 
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")
        
        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where title like '%" + keyword + "%'"

        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelime bulunamadı", "warning")
            return redirect(url_for("articles_page"))
        else:
            articles = cursor.fetchall()
            return render_template("article.html",articles=articles)



if __name__ == "__main__":
    app.run(debug=True)

