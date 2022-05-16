#renderiza las vistas al usuario
from django.shortcuts import render
# para redirigir a otras paginas
from django.http import HttpResponseRedirect, HttpResponse,FileResponse
#el formulario de login
from .forms import *
# clase para crear vistas basadas en sub-clases
from django.views import View
#autentificacion de usuario e inicio de sesion
from django.contrib.auth import authenticate, login, logout
#verifica si el usuario esta logeado
from django.contrib.auth.mixins import LoginRequiredMixin

#modelos
from .models import *
#formularios dinamicos
from django.forms import formset_factory
#funciones personalizadas
from .funciones import *
#Mensajes de formulario
from django.contrib import messages
#Ejecuta un comando en la terminal externa
from django.core.management import call_command
#procesa archivos en .json
from django.core import serializers
#permite acceder de manera mas facil a los ficheros
from django.core.files.storage import FileSystemStorage


#Vistas endogenas.


#Interfaz de inicio de sesion----------------------------------------------------#
class Login(View):
    #Si el usuario ya envio el formulario por metodo post
    def post(self,request):
        # Crea una instancia del formulario y la llena con los datos:
        form = LoginFormulario(request.POST)
        # Revisa si es valido:
        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            usuario = form.cleaned_data['username']
            clave = form.cleaned_data['password']
            # Se verifica que el usuario y su clave existan
            logeado = authenticate(request, username=usuario, password=clave)
            if logeado is not None:
                login(request,logeado)
                #Si el login es correcto lo redirige al panel del sistema:
                return HttpResponseRedirect('/inventario/panel')
            else:
                #De lo contrario lanzara el mismo formulario
                return render(request, 'inventario/login.html', {'form': form})

    # Si se llega por GET crearemos un formulario en blanco
    def get(self,request):
        if request.user.is_authenticated == True:
            return HttpResponseRedirect('/inventario/panel')

        form = LoginFormulario()
        #Envia al usuario el formulario para que lo llene
        return render(request, 'inventario/login.html', {'form': form})
#Fin de vista---------------------------------------------------------------------#        




#Panel de inicio y vista principal------------------------------------------------#
class Panel(LoginRequiredMixin, View):
    #De no estar logeado, el usuario sera redirigido a la pagina de Login
    #Las dos variables son la pagina a redirigir y el campo adicional, respectivamente
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from datetime import date
        #Recupera los datos del usuario despues del login
        contexto = {'usuario': request.user.username,
                    'id_usuario':request.user.id,
                   'nombre': request.user.first_name,
                   'apellido': request.user.last_name,
                   'correo': request.user.email,
                   'fecha':  date.today(),
                   'productosRegistrados' : Producto.numeroRegistrados(),
                   'productosVendidos' :  DetalleFactura.productosVendidos(),
                   'clientesRegistrados' : Cliente.numeroRegistrados(),
                   'usuariosRegistrados' : Usuario.numeroRegistrados(),
                   'facturasEmitidas' : Factura.numeroRegistrados(),
                   'ingresoTotal' : Factura.ingresoTotal(),
                   'ultimasVentas': DetalleFactura.ultimasVentas(),
                   'administradores': Usuario.numeroUsuarios('administrador'),
                   'usuarios': Usuario.numeroUsuarios('usuario')

        }


        return render(request, 'inventario/panel.html',contexto)
#Fin de vista----------------------------------------------------------------------#




#Maneja la salida del usuario------------------------------------------------------#
class Salir(LoginRequiredMixin, View):
    #Sale de la sesion actual
    login_url = 'inventario/login'
    redirect_field_name = None

    def get(self, request):
        logout(request)
        return HttpResponseRedirect('/inventario/login')
#Fin de vista----------------------------------------------------------------------#


#Muestra el perfil del usuario logeado actualmente---------------------------------#
class Perfil(LoginRequiredMixin, View):
    login_url = 'inventario/login'
    redirect_field_name = None

    #se accede al modo adecuado y se valida al usuario actual para ver si puede modificar al otro usuario-
    #-el cual es obtenido por la variable 'p'
    def get(self, request, modo, p):
        if modo == 'editar':
            perf = Usuario.objects.get(id=p)
            editandoSuperAdmin = False

            if p == 1:
                if request.user.nivel != 2:
                    messages.error(request, 'No puede editar el perfil del administrador por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p)
                editandoSuperAdmin = True
            else:
                if request.user.is_superuser != True: 
                    messages.error(request, 'No puede cambiar el perfil por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 

                else:
                    if perf.is_superuser == True:
                        if request.user.nivel == 2:
                            pass

                        elif perf.id != request.user.id:
                            messages.error(request, 'No puedes cambiar el perfil de un usuario de tu mismo nivel')

                            return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 

            if editandoSuperAdmin:
                form = UsuarioFormulario()
                form.fields['level'].disabled = True
            else:
                form = UsuarioFormulario()

            #Me pregunto si habia una manera mas facil de hacer esto, solo necesitaba hacer que el formulario-
            #-apareciera lleno de una vez, pero arrojaba User already exists y no pasaba de form.is_valid()
            form['username'].field.widget.attrs['value']  = perf.username
            form['first_name'].field.widget.attrs['value']  = perf.first_name
            form['last_name'].field.widget.attrs['value']  = perf.last_name
            form['email'].field.widget.attrs['value']  = perf.email
            form['level'].field.widget.attrs['value']  = perf.nivel

            #Envia al usuario el formulario para que lo llene
            contexto = {'form':form,'modo':request.session.get('perfilProcesado'),'editar':'perfil',
            'nombreUsuario':perf.username}

            contexto = complementarContexto(contexto,request.user)
            return render(request,'inventario/perfil/perfil.html', contexto)


        elif modo == 'clave':  
            perf = Usuario.objects.get(id=p)
            if p == 1:
                if request.user.nivel != 2:
                   
                    messages.error(request, 'No puede cambiar la clave del administrador por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p)  
            else:
                if request.user.is_superuser != True: 
                    messages.error(request, 'No puede cambiar la clave de este perfil por no tener los permisos suficientes')
                    return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 

                else:
                    if perf.is_superuser == True:
                        if request.user.nivel == 2:
                            pass

                        elif perf.id != request.user.id:
                            messages.error(request, 'No puedes cambiar la clave de un usuario de tu mismo nivel')
                            return HttpResponseRedirect('/inventario/perfil/ver/%s' % p) 


            form = ClaveFormulario(request.POST)
            contexto = { 'form':form, 'modo':request.session.get('perfilProcesado'),
            'editar':'clave','nombreUsuario':perf.username }            

            contexto = complementarContexto(contexto,request.user)
            return render(request, 'inventario/perfil/perfil.html', contexto)

        elif modo == 'ver':
            perf = Usuario.objects.get(id=p)
            contexto = { 'perfil':perf }      
            contexto = complementarContexto(contexto,request.user)
          
            return render(request,'inventario/perfil/verPerfil.html', contexto)



    def post(self,request,modo,p):
        if modo ==  'editar':
            # Crea una instancia del formulario y la llena con los datos:
            form = UsuarioFormulario(request.POST)
            # Revisa si es valido:
            
            if form.is_valid():
                perf = Usuario.objects.get(id=p)
                # Procesa y asigna los datos con form.cleaned_data como se requiere
                if p != 1:
                    level = form.cleaned_data['level']        
                    perf.nivel = level
                    perf.is_superuser = level

                username = form.cleaned_data['username']
                first_name = form.cleaned_data['first_name']
                last_name = form.cleaned_data['last_name']
                email = form.cleaned_data['email']

                perf.username = username
                perf.first_name = first_name
                perf.last_name = last_name
                perf.email = email

                perf.save()
                
                form = UsuarioFormulario()
                messages.success(request, 'Actualizado exitosamente el perfil de ID %s.' % p)
                request.session['perfilProcesado'] = True           
                return HttpResponseRedirect("/inventario/perfil/ver/%s" % perf.id)
            else:
                #De lo contrario lanzara el mismo formulario
                return render(request, 'inventario/perfil/perfil.html', {'form': form})

        elif modo == 'clave':
            form = ClaveFormulario(request.POST)

            if form.is_valid():
                error = 0
                clave_nueva = form.cleaned_data['clave_nueva']
                repetir_clave = form.cleaned_data['repetir_clave']
                #clave = form.cleaned_data['clave']

                #Comentare estas lineas de abajo para deshacerme de la necesidad
                #   de obligar a que el usuario coloque la clave nuevamente
                #correcto = authenticate(username=request.user.username , password=clave)


                #if correcto is not None:
                    #if clave_nueva != clave:
                        #pass
                    #else:
                        #error = 1
                        #messages.error(request,"La clave nueva no puede ser identica a la actual") 

                usuario = Usuario.objects.get(id=p) 

                if clave_nueva == repetir_clave:
                    pass
                else:
                    error = 1
                    messages.error(request,"La clave nueva y su repeticion tienen que coincidir")

                #else:
                    #error = 1
                    #messages.error(request,"La clave de acceso actual que ha insertado es incorrecta")

                if(error == 0):
                    messages.success(request, 'La clave se ha cambiado correctamente!')
                    usuario.set_password(clave_nueva)
                    usuario.save()
                    return HttpResponseRedirect("/inventario/login")

                else:
                    return HttpResponseRedirect("/inventario/perfil/clave/%s" % p)
    



  
#----------------------------------------------------------------------------------#   





#Muestra una lista de 10 productos por pagina----------------------------------------#
class ListarProductos(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models

        #Lista de productos de la BDD
        productos = Producto.objects.all()
                               
        contexto = {'tabla':productos}

        contexto = complementarContexto(contexto,request.user)  

        return render(request, 'inventario/producto/listarProductos.html',contexto)
#Fin de vista-------------------------------------------------------------------------#








#Crea una lista de los clientes, 10 por pagina----------------------------------------#
class ListarClientes(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models
        #Saca una lista de todos los clientes de la BDD
        clientes = Cliente.objects.all()                
        contexto = {'tabla': clientes}
        contexto = complementarContexto(contexto,request.user)         

        return render(request, 'inventario/cliente/listarClientes.html',contexto) 
#Fin de vista--------------------------------------------------------------------------#




#Muestra y procesa los detalles de cada producto de la factura--------------------------------#
class ListarFacturas(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        #Lista de productos de la BDD
        facturas = Factura.objects.all()
        #Crea el paginador
                               
        contexto = {'tabla': facturas}
        contexto = complementarContexto(contexto,request.user) 

        return render(request, 'inventario/factura/listarFacturas.html', contexto)        

#Fin de vista---------------------------------------------------------------------------------------#     




#Crea una lista de los clientes, 10 por pagina----------------------------------------#
class ListarProveedores(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models
        #Saca una lista de todos los clientes de la BDD
        proveedores = Proveedor.objects.all()                
        contexto = {'tabla': proveedores}
        contexto = complementarContexto(contexto,request.user)         

        return render(request, 'inventario/proveedor/listarProveedores.html',contexto) 
#Fin de vista--------------------------------------------------------------------------#







#Lista todos los pedidos---------------------------------------------------------------------------# 
class ListarPedidos(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        from django.db import models
        #Saca una lista de todos los clientes de la BDD
        pedidos = Pedido.objects.all()                
        contexto = {'tabla': pedidos}
        contexto = complementarContexto(contexto,request.user)         

        return render(request, 'inventario/pedido/listarPedidos.html',contexto) 

#------------------------------------------------------------------------------------------------#




#Crea un nuevo usuario--------------------------------------------------------------#
class CrearUsuario(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None    

    def get(self, request):
        if request.user.is_superuser:
            form = NuevoUsuarioFormulario()
            #Envia al usuario el formulario para que lo llene
            contexto = {'form':form , 'modo':request.session.get('usuarioCreado')}   
            contexto = complementarContexto(contexto,request.user)  
            return render(request, 'inventario/usuario/crearUsuario.html', contexto)
        else:
            messages.error(request, 'No tiene los permisos para crear un usuario nuevo')
            return HttpResponseRedirect('/inventario/panel')

    def post(self, request):
        form = NuevoUsuarioFormulario(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            rep_password = form.cleaned_data['rep_password']
            level = form.cleaned_data['level']

            error = 0

            if password == rep_password:
                pass

            else:
                error = 1
                messages.error(request, 'La clave y su repeticion tienen que coincidir')

            if usuarioExiste(Usuario,'username',username) is False:
                pass

            else:
                error = 1
                messages.error(request, "El nombre de usuario '%s' ya existe. eliga otro!" % username)


            if usuarioExiste(Usuario,'email',email) is False:
                pass

            else:
                error = 1
                messages.error(request, "El correo '%s' ya existe. eliga otro!" % email)                    

            if(error == 0):
                if level == '0':
                    nuevoUsuario = Usuario.objects.create_user(username=username,password=password,email=email)
                    nivel = 0
                elif level == '1':
                    nuevoUsuario = Usuario.objects.create_superuser(username=username,password=password,email=email)
                    nivel = 1

                nuevoUsuario.first_name = first_name
                nuevoUsuario.last_name = last_name
                nuevoUsuario.nivel = nivel
                nuevoUsuario.save()

                messages.success(request, 'Usuario creado exitosamente')
                return HttpResponseRedirect('/inventario/crearUsuario')

            else:
                return HttpResponseRedirect('/inventario/crearUsuario')
                        
                   



#Fin de vista----------------------------------------------------------------------


#Lista todos los usuarios actuales--------------------------------------------------------------#
class ListarUsuarios(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None    

    def get(self, request):
        usuarios = Usuario.objects.all()
        #Envia al usuario el formulario para que lo llene
        contexto = {'tabla':usuarios}   
        contexto = complementarContexto(contexto,request.user)  
        return render(request, 'inventario/usuario/listarUsuarios.html', contexto)

    def post(self, request):
        pass   

#Fin de vista----------------------------------------------------------------------



#Importa toda la base de datos, primero crea una copia de la actual mientras se procesa la nueva--#
class ImportarBDD(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        if request.user.is_superuser == False:
            messages.error(request, 'Solo los administradores pueden importar una nueva base de datos')  
            return HttpResponseRedirect('/inventario/panel')

        form = ImportarBDDFormulario()
        contexto = { 'form': form }
        contexto = complementarContexto(contexto, request.user)
        return render(request, 'inventario/BDD/importar.html', contexto)

    def post(self, request):
        form = ImportarBDDFormulario(request.POST, request.FILES)

        if form.is_valid():
            ruta = 'inventario/archivos/BDD/inventario_respaldo.xml'
            manejarArchivo(request.FILES['archivo'],ruta)

            try:
                call_command('loaddata', ruta, verbosity=0)
                messages.success(request, 'Base de datos subida exitosamente')
                return HttpResponseRedirect('/inventario/importarBDD')
            except Exception:
                messages.error(request, 'El archivo esta corrupto')
                return HttpResponseRedirect('/inventario/importarBDD')





#Fin de vista--------------------------------------------------------------------------------




#Configuracion general de varios elementos--------------------------------------------------#
class ConfiguracionGeneral(LoginRequiredMixin, View):
    login_url = '/inventario/login'
    redirect_field_name = None

    def get(self, request):
        conf = Opciones.objects.get(id=1)
        form = OpcionesFormulario()
        
        #Envia al usuario el formulario para que lo llene

        form['moneda'].field.widget.attrs['value']  = conf.moneda
        form['valor_iva'].field.widget.attrs['value']  = conf.valor_iva
        form['mensaje_factura'].field.widget.attrs['value']  = conf.mensaje_factura
        form['nombre_negocio'].field.widget.attrs['value']  = conf.nombre_negocio

        contexto = {'form':form}    
        contexto = complementarContexto(contexto,request.user) 
        return render(request, 'inventario/opciones/configuracion.html', contexto)

    def post(self,request):
        # Crea una instancia del formulario y la llena con los datos:
        form = OpcionesFormulario(request.POST,request.FILES)
        # Revisa si es valido:

        if form.is_valid():
            # Procesa y asigna los datos con form.cleaned_data como se requiere
            moneda = form.cleaned_data['moneda']
            valor_iva = form.cleaned_data['valor_iva']
            mensaje_factura = form.cleaned_data['mensaje_factura']
            nombre_negocio = form.cleaned_data['nombre_negocio']
            imagen = request.FILES.get('imagen',False)

            #Si se subio un logo se sobreescribira en la carpeta ubicada
            #--en la siguiente ruta
            if imagen:
                manejarArchivo(imagen,'inventario/static/inventario/assets/logo/logo2.png')

            conf = Opciones.objects.get(id=1)
            conf.moneda = moneda
            conf.valor_iva = valor_iva
            conf.mensaje_factura = mensaje_factura
            conf.nombre_negocio = nombre_negocio
            conf.save()


            messages.success(request, 'Configuracion actualizada exitosamente!')          
            return HttpResponseRedirect("/inventario/configuracionGeneral")
        else:
            form = OpcionesFormulario(instance=conf)
            #De lo contrario lanzara el mismo formulario
            return render(request, 'inventario/opciones/configuracion.html', {'form': form})

#Fin de vista--------------------------------------------------------------------------------

