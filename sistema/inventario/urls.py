from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
path('login', views.Login.as_view(), name='login'),
path('panel', views.Panel.as_view(), name='panel'),
path('salir', views.Salir.as_view(), name='salir'),
path('perfil/<str:modo>/<int:p>', views.Perfil.as_view(), name='perfil'),

path('listarProductos', views.ListarProductos.as_view(), name='listarProductos'),


path('listarProveedores', views.ListarProveedores.as_view(), name='listarProveedores'),



path('listarPedidos', views.ListarPedidos.as_view(), name='listarPedidos'),



path('listarClientes', views.ListarClientes.as_view(), name='listarClientes'),



path('listarFacturas',views.ListarFacturas.as_view(), name='listarFacturas'),



path('crearUsuario',views.CrearUsuario.as_view(), name='crearUsuario'),
path('listarUsuarios', views.ListarUsuarios.as_view(), name='listarUsuarios'),


]

