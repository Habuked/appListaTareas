from flask import Flask, render_template, request, session, redirect, url_for
import config
from datetime import datetime
from flask_mysqldb import MySQL
from flask_mail import Mail, Message

def crear_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.HEX_SEC_KEY
    app.config['MYSQL_HOST'] = config.MYSQL_HOST
    app.config['MYSQL_USER'] = config.MYSQL_USER
    app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
    app.config['MYSQL_DB'] = config.MYSQL_DB


    app.config['MAIL_SERVER']= 'smtp-mail.outlook.com'
    app.config['MAIL_PORT'] = config.MAIL_PORT
    app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
    app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False

    #instanciar la conexion de mysql
    mysql = MySQL(app)

    #instanciar la conexion de mail
    mail = Mail(app)

    @app.route('/')
    def index():
        return render_template("index.html")

    @app.route('/reset')
    def reset():
        return render_template("reset.html")

    @app.route('/login', methods = ['POST'])
    def login():
        
        #esto lo use para probar el metodo POST para comprobar que viaje los campos
        #usuario y password desde index.html a tareas.html
        email = request.form['email']
        password = request.form['password']

        #creo al conexion a la base de datos
        conexion = mysql.connection.cursor()

        #generar la consulta
        conexion.execute(
                            "SELECT * FROM usuarios WHERE email=%s AND password= %s", 
                        (email, password)
                        )
        
        #obtengo informacion del select y la guardo en la variable usuarios
        usuarios = conexion.fetchone()

        #cierro la conexion a la base de datos
        conexion.close()


        #validar si existe el usuario
        if usuarios is not None:
            session['email'] = email
            session['nombre'] = usuarios[2]
            session['apellido'] = usuarios[3]
            session['sexo'] = usuarios[4]

            #si existe usuario, redirecciona a tareas.html
            return redirect(url_for('tareas'))
        else:
            #si no existe, envia a index.html + un mensaje indicando que esta incorrecta credenciales
            return render_template("index.html", mensaje="Usuario y/o password incorrectos") 
        
        #return render_template("tareas.html", email=email, password=password)

    @app.route('/send_mail', methods = ['GET', 'POST'])
    def send_mail():

        email = request.form['email']
        conexion = mysql.connection.cursor()
        resultado = conexion.execute("SELECT password FROM usuarios WHERE email = %s", [email])
        resultado = conexion.fetchone()

        if resultado:
            password = resultado[0];
        else:
            error = "Email no existe !!"
            

        if request.method == 'POST':
            mail_message = Message("RESET DE PASSWORD -- APP ListaTareas", sender='javier_sanchez16@hotmail.com', recipients=[email])
            mail_message.body = "Gracias por contactarnos, tu password es: " + password
            
            mail.send(mail_message)
            #return 'mensaje enviado'

        conexion.close()
        return render_template('index.html', mensaje = 'Revise su email con la nueva contraseña.')

    @app.route('/tareas')
    def tareas():


        email = session['email']
        conexion = mysql.connection.cursor()
        conexion.execute("SELECT * FROM tareas WHERE email = %s", [email])
        tareas = conexion.fetchall()

        #print(tareas)
        mysql.connection.commit() 
        insertObject = []
        columnNames = [column[0] for column in conexion.description]

        for record in tareas:
            insertObject.append(dict(zip(columnNames, record)))
        conexion.close()
            

        return render_template("tareas.html", tareas = insertObject)

    @app.route('/registro')
    def registro():
        return render_template("registro.html")

    @app.route('/logout')
    def logout():
        #para borrar las sessiones generadas, las sesiones continen el email, nombre y apellido del usuario
        session.clear()
        return redirect(url_for('index'))

    @app.route('/nuevo-usuario', methods=['POST'])
    def nuevoUsuario():
        email = request.form['email']

        password = request.form['password']
        passwordConfirmado = request.form['confirm-password']

        if password != passwordConfirmado:
            return render_template("registro.html", mensaje="La contraseña de verificación no coincide") 

        nombre = request.form['nombre']
        apellido = request.form['apellido']
        sexo = request.form['sexo']


        if email and password and nombre and apellido and sexo:
            conexion = mysql.connection.cursor()
            sql = 'INSERT INTO usuarios (email, password, nombre, apellido, sexo) VALUES (%s, %s, %s, %s, %s)'
            data = (email, password, nombre, apellido, sexo)
            conexion.execute(sql, data)
            mysql.connection.commit()
        return redirect(url_for('index'))

    @app.route('/nueva-tarea', methods=['POST'])
    def nuevaTarea():
        tituloTarea = request.form['tituloTarea']
        estado = request.form['estado']
        categoria = request.form['categoria']
        descripcion = request.form['descripcion']
        email = session['email']
        d = datetime.now()
        fechaTarea = d.strftime("%Y-%m-%d $H:%M:%S")

        if tituloTarea and estado and categoria and descripcion and email:
            conexion = mysql.connection.cursor()
            sql = 'INSERT INTO tareas (tituloTarea, estado, categoria, descripcion, email, fechaTarea) VALUES (%s, %s, %s, %s, %s, %s)'
            data = (tituloTarea, estado, categoria, descripcion, email, fechaTarea)
            conexion.execute(sql, data)
            mysql.connection.commit()
        return redirect(url_for('tareas'))


    @app.route('/editar/<int:id>')
    def editar(id):
        

        email = session['email']
        conexion = mysql.connection.cursor()
        conexion.execute("SELECT * FROM tareas WHERE codigoTarea = %s and email = %s", [id, email])
        tareas = conexion.fetchall()

        print(tareas)
        mysql.connection.commit() 

        #return render_template("tareas.html", tareas = tareas)
        return render_template("editar.html", tareas = tareas)

    @app.route('/actualizar/<int:id>', methods=['POST'])
    def actualizar(id):

        #codigoTarea = request.form['codigoTarea']
        
        tituloTarea = request.form['tituloTarea']
        estado = request.form['estado']
        categoria = request.form['categoria']
        descripcion = request.form['descripcion']
        email = session['email']
        d = datetime.now()
        fechaTarea = d.strftime("%Y-%m-%d $H:%M:%S")

        if tituloTarea and estado and categoria and descripcion and email:
            conexion = mysql.connection.cursor()
            sql = 'UPDATE tareas SET tituloTarea= %s, estado = %s, categoria =%s, descripcion = %s, email= %s, fechaTarea = %s WHERE codigoTarea = %s'
            data = (tituloTarea, estado, categoria, descripcion, email, fechaTarea, id)
            conexion.execute(sql, data)
            mysql.connection.commit()

        return redirect(url_for('tareas'))
        
    @app.route('/eliminar/<int:id>', methods=['POST'])
    def eliminar(id):

        conexion = mysql.connection.cursor()
        conexion.execute("DELETE FROM tareas WHERE codigoTarea = %s", [id])
        mysql.connection.commit() 

        return redirect(url_for('tareas'))

    return app



if __name__ == "__main__":
    app = crear_app()
    app.run()
    #app.run(debug=True)
