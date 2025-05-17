from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Sum
from django.urls import reverse
from django.utils import timezone
from django.db import models  # Añade esta importación
from django.urls import path
from .models import *
from .views import crear_venta_desde_cita
from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.admin import AdminSite
# Importar los modelos
from .models import (
    Cliente, Empleado, Servicio, Cita, DetalleCita,
    Producto, Venta, DetalleVenta, MovimientoInventario,
    HorarioEmpleado, Auditoria
)


# Cliente Admin
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'telefono', 'email', 'fecha_registro', 'ultima_visita', 'activo')
    list_filter = ('activo', 'fecha_registro')
    search_fields = ('nombre', 'apellido', 'telefono', 'email')
    date_hierarchy = 'fecha_registro'
    readonly_fields = ('fecha_registro', 'ultima_visita')
    fieldsets = (
        ('Información Personal', {
            'fields': (('nombre', 'apellido'), 'fecha_nacimiento', ('telefono', 'email'), 'direccion')
        }),
        ('Información de Barbería', {
            'fields': ('preferencias', 'historial_notas')
        }),
        ('Estado', {
            'fields': ('activo', ('fecha_registro', 'ultima_visita'))
        }),
    )
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    
    actions = ['marcar_como_activo', 'marcar_como_inactivo']
    
    def marcar_como_activo(self, request, queryset):
        queryset.update(activo=True)
    marcar_como_activo.short_description = "Marcar clientes seleccionados como activos"
    
    def marcar_como_inactivo(self, request, queryset):
        queryset.update(activo=False)
    marcar_como_inactivo.short_description = "Marcar clientes seleccionados como inactivos"

# DetalleCita Inline para Cita Admin
class DetalleCitaInline(admin.TabularInline):
    model = DetalleCita
    extra = 1
    fields = ('servicio', 'precio_aplicado', 'duracion_minutos', 'notas')
    autocomplete_fields = ['servicio']

# Cita Admin
class CitaAdmin(admin.ModelAdmin):
    list_display = ('cita_id', 'cliente_nombre', 'empleado_nombre', 'fecha_hora', 'duracion_total', 'estado', 'acciones')
    list_filter = ('estado', 'fecha_hora', 'empleado')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'empleado__nombre', 'empleado__apellido')
    readonly_fields = ('fecha_creacion', 'duracion_total')
    date_hierarchy = 'fecha_hora'
    inlines = [DetalleCitaInline]
    autocomplete_fields = ['cliente', 'empleado']
    
    fieldsets = (
        ('Información de la Cita', {
            'fields': (('cliente', 'empleado'), 'fecha_hora', 'duracion_total', 'estado')
        }),
        ('Detalles', {
            'fields': ('notas', 'fecha_creacion')
        }),
    )
    
    def cliente_nombre(self, obj):
        if obj.cliente:
            return f"{obj.cliente.nombre} {obj.cliente.apellido}"
        return "Sin cliente"
    cliente_nombre.short_description = 'Cliente'
    
    def empleado_nombre(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"
    empleado_nombre.short_description = 'Empleado'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/crear-venta/',
                self.admin_site.admin_view(crear_venta_desde_cita),
                name='crear_venta',
            ),
        ]
        return custom_urls + urls
    
    def acciones(self, obj):
        btns = []
        if obj.estado == 'completada':
        # Verificar si tiene venta asociada
            try:
                venta = Venta.objects.get(cita=obj)
                btns.append(
                f'<a class="button" href="{reverse("admin:barberia_app_venta_change", args=[venta.pk])}">'
                f'<i class="fas fa-eye"></i> Ver Venta</a>'
            )
            except Venta.DoesNotExist:
            # Construir la URL directamente
                btns.append(
                f'<a class="button" href="/admin/barberia_app/cita/{obj.pk}/crear-venta/">'
                f'<i class="fas fa-cash-register"></i> Generar Venta</a>'
                )
    
        return format_html('&nbsp;'.join(btns)) if btns else '-'
    acciones.short_description = 'Acciones'
    
    actions = ['marcar_como_completada', 'marcar_como_cancelada', 'marcar_como_no_asistio']
    
    def marcar_como_completada(self, request, queryset):
        queryset.update(estado='completada')
    marcar_como_completada.short_description = "Marcar como completadas"
    
    def marcar_como_cancelada(self, request, queryset):
        queryset.update(estado='cancelada')
    marcar_como_cancelada.short_description = "Marcar como canceladas"
    
    def marcar_como_no_asistio(self, request, queryset):
        queryset.update(estado='no_asistio')
    marcar_como_no_asistio.short_description = "Marcar como no asistió"

# Horario Empleado Inline
class HorarioEmpleadoInline(admin.TabularInline):
    model = HorarioEmpleado
    extra = 1
    fields = ('dia_semana', 'hora_inicio', 'hora_fin', 'es_descanso')

# Empleado Admin
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'puesto', 'especialidad', 'telefono', 'estado', 'fecha_contratacion')
    list_filter = ('estado', 'puesto', 'especialidad')
    search_fields = ('nombre', 'apellido', 'telefono', 'email', 'especialidad')
    date_hierarchy = 'fecha_contratacion'
    inlines = [HorarioEmpleadoInline]
    
    fieldsets = (
        ('Información Personal', {
            'fields': (('nombre', 'apellido'), ('telefono', 'email'))
        }),
        ('Información Laboral', {
            'fields': ('puesto', 'especialidad', 'fecha_contratacion', 'porcentaje_comision', 'estado')
        }),
    )
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    
    actions = ['marcar_como_activo', 'marcar_como_inactivo', 'marcar_como_vacaciones']
    
    def marcar_como_activo(self, request, queryset):
        queryset.update(estado='activo')
    marcar_como_activo.short_description = "Marcar como activos"
    
    def marcar_como_inactivo(self, request, queryset):
        queryset.update(estado='inactivo')
    marcar_como_inactivo.short_description = "Marcar como inactivos"
    
    def marcar_como_vacaciones(self, request, queryset):
        queryset.update(estado='vacaciones')
    marcar_como_vacaciones.short_description = "Marcar en vacaciones"

# Servicio Admin
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'duracion_minutos', 'precio', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'descripcion', 'categoria')
    list_editable = ('precio', 'activo')
    
    fieldsets = (
        ('Información del Servicio', {
            'fields': ('nombre', 'categoria', 'descripcion')
        }),
        ('Precios y Tiempos', {
            'fields': ('precio', 'duracion_minutos')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
    )
    
    actions = ['marcar_como_activo', 'marcar_como_inactivo']
    
    def marcar_como_activo(self, request, queryset):
        queryset.update(activo=True)
    marcar_como_activo.short_description = "Marcar como activos"
    
    def marcar_como_inactivo(self, request, queryset):
        queryset.update(activo=False)
    marcar_como_inactivo.short_description = "Marcar como inactivos"

# Producto Admin
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'marca', 'categoria', 'precio_venta', 'stock_actual', 'estado_stock', 'activo')
    list_filter = ('categoria', 'marca', 'para_venta', 'activo')
    search_fields = ('nombre', 'descripcion', 'marca', 'categoria')
    list_editable = ('precio_venta',)
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', ('marca', 'categoria'), 'descripcion')
        }),
        ('Precios', {
            'fields': (('precio_venta', 'precio_costo'),)
        }),
        ('Inventario', {
            'fields': (('stock_actual', 'stock_minimo'), 'unidad_medida')
        }),
        ('Estado', {
            'fields': ('para_venta', 'activo')
        }),
    )
    
    def estado_stock(self, obj):
        if obj.stock_actual <= 0:
            return format_html('<span style="color: red; font-weight: bold;">SIN STOCK</span>')
        elif obj.stock_actual <= obj.stock_minimo:
            return format_html('<span style="color: orange; font-weight: bold;">BAJO</span>')
        else:
            return format_html('<span style="color: green;">OK</span>')
    estado_stock.short_description = 'Estado Stock'

# DetalleVenta Inline para Venta Admin
class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    fields = ('tipo', 'producto', 'servicio', 'cantidad', 'precio_unitario', 'descuento_aplicado', 'subtotal_linea')
    readonly_fields = ('subtotal_linea',)
    autocomplete_fields = ['producto', 'servicio']

# Venta Admin
class VentaAdmin(admin.ModelAdmin):
    list_display = ('venta_id', 'fecha_hora', 'cliente_nombre', 'empleado_nombre', 'total', 'metodo_pago', 'estado')
    list_filter = ('estado', 'metodo_pago', 'fecha_hora', 'empleado')
    search_fields = ('cliente__nombre', 'cliente__apellido', 'empleado__nombre')
    readonly_fields = ('subtotal', 'impuestos', 'total')
    date_hierarchy = 'fecha_hora'
    inlines = [DetalleVentaInline]
    autocomplete_fields = ['cliente', 'empleado', 'cita']
    
    fieldsets = (
        ('Información de la Venta', {
            'fields': (('cliente', 'empleado'), 'fecha_hora', 'cita')
        }),
        ('Detalles de Pago', {
            'fields': (('subtotal', 'impuestos', 'descuentos'), 'total', 'metodo_pago', 'estado')
        }),
        ('Notas', {
            'fields': ('notas',)
        }),
    )
    
    def cliente_nombre(self, obj):
        if obj.cliente:
            return f"{obj.cliente.nombre} {obj.cliente.apellido}"
        return "Sin cliente"
    cliente_nombre.short_description = 'Cliente'
    
    def empleado_nombre(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"
    empleado_nombre.short_description = 'Empleado'
    
    actions = ['marcar_como_anulada', 'marcar_como_reembolsada']
    
    def marcar_como_anulada(self, request, queryset):
        queryset.update(estado='anulada')
    marcar_como_anulada.short_description = "Marcar como anuladas"
    
    def marcar_como_reembolsada(self, request, queryset):
        queryset.update(estado='reembolsada')
    marcar_como_reembolsada.short_description = "Marcar como reembolsadas"
    
    def save_model(self, request, obj, form, change):
        # Calcular totales antes de guardar
        if not change:  # Solo si es nuevo
            obj.subtotal = sum(detalle.subtotal_linea for detalle in obj.detalleventa_set.all())
            obj.total = obj.subtotal + obj.impuestos - obj.descuentos
        super().save_model(request, obj, form, change)

# MovimientoInventario Admin
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('movimiento_id', 'producto', 'tipo_movimiento', 'cantidad', 'fecha_hora', 'empleado_nombre', 'referencia')
    list_filter = ('tipo_movimiento', 'fecha_hora', 'producto__categoria')
    search_fields = ('producto__nombre', 'motivo', 'documento_referencia')
    date_hierarchy = 'fecha_hora'
    autocomplete_fields = ['producto', 'empleado', 'venta']
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('producto', 'tipo_movimiento', 'cantidad', 'fecha_hora')
        }),
        ('Referencias', {
            'fields': ('empleado', 'venta', 'motivo', 'documento_referencia')
        }),
    )
    
    def empleado_nombre(self, obj):
        if obj.empleado:
            return f"{obj.empleado.nombre} {obj.empleado.apellido}"
        return "-"
    empleado_nombre.short_description = 'Empleado'
    
    def referencia(self, obj):
        if obj.venta:
            return f"Venta #{obj.venta.venta_id}"
        if obj.documento_referencia:
            return obj.documento_referencia
        return obj.motivo or "-"
    referencia.short_description = 'Referencia'

# HorarioEmpleado Admin
class HorarioEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado_nombre', 'dia_semana_nombre', 'hora_inicio', 'hora_fin', 'es_descanso')
    list_filter = ('dia_semana', 'es_descanso', 'empleado')
    autocomplete_fields = ['empleado']
    
    def empleado_nombre(self, obj):
        return f"{obj.empleado.nombre} {obj.empleado.apellido}"
    empleado_nombre.short_description = 'Empleado'
    
    def dia_semana_nombre(self, obj):
        return obj.get_dia_semana_display()
    dia_semana_nombre.short_description = 'Día'

# Auditoria Admin
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('log_id', 'tabla_afectada', 'operacion', 'registro_id', 'fecha_hora', 'usuario_db')
    list_filter = ('tabla_afectada', 'operacion', 'fecha_hora')
    search_fields = ('tabla_afectada', 'registro_id', 'usuario_db', 'usuario_app')
    date_hierarchy = 'fecha_hora'
    readonly_fields = ('log_id', 'tabla_afectada', 'operacion', 'registro_id', 
                     'datos_antiguos', 'datos_nuevos', 'usuario_db', 
                     'usuario_app', 'fecha_hora', 'ip_origen')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

# Registrar los modelos con sus clases Admin
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Empleado, EmpleadoAdmin)
admin.site.register(Servicio, ServicioAdmin)
admin.site.register(Cita, CitaAdmin)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Venta, VentaAdmin)
admin.site.register(MovimientoInventario, MovimientoInventarioAdmin)
admin.site.register(HorarioEmpleado, HorarioEmpleadoAdmin)
admin.site.register(Auditoria, AuditoriaAdmin)

# Personalización del Admin
admin.site.site_header = "Administración de Barbería"
admin.site.site_title = "Panel de Barbería"
admin.site.index_title = "Bienvenido al Sistema de Gestión"

# En tu archivo admin.py

from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta

# Importaciones adicionales
from django.contrib import admin
from django.urls import path

# Clase para el Dashboard personalizado
class DashboardView(TemplateView):
    template_name = 'admin/dashboard.html'
    
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        # Establecer el admin_site antes de cualquier procesamiento
        self.admin_site = barberia_admin_site
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        
        
        # Citas del día
        context['citas_hoy'] = Cita.objects.filter(
            fecha_hora__date=today
        ).order_by('fecha_hora')
        
        # Empleados disponibles hoy
        context['empleados_disponibles'] = Empleado.objects.filter(
            estado='activo'
        )
        
        # Productos con bajo stock
        context['productos_bajo_stock'] = Producto.objects.filter(
        stock_actual__lte=models.F('stock_minimo'),
        activo=True
        )
        
        # Ventas del día
        context['ventas_hoy'] = Venta.objects.filter(
            fecha_hora__date=today, 
            estado='completada'
        )
        
        # Total ventas hoy
        context['total_ventas_hoy'] = context['ventas_hoy'].aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Ventas de la semana
        semana_pasada = today - timedelta(days=7)
        context['ventas_semana'] = Venta.objects.filter(
            fecha_hora__date__gte=semana_pasada,
            fecha_hora__date__lte=today,
            estado='completada'
        )
        
        # Total ventas semana
        context['total_ventas_semana'] = context['ventas_semana'].aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Servicios más solicitados
        context['servicios_populares'] = DetalleVenta.objects.filter(
            tipo='servicio',
            venta__estado='completada'
        ).values('servicio__nombre').annotate(
            total=Count('servicio')
        ).order_by('-total')[:5]
        
        # Productos más vendidos
        context['productos_populares'] = DetalleVenta.objects.filter(
            tipo='producto',
            venta__estado='completada'
        ).values('producto__nombre').annotate(
            total=Count('producto')
        ).order_by('-total')[:5]
        
        # Actividad reciente
        context['actividad_reciente'] = Auditoria.objects.all().order_by('-fecha_hora')[:10]
        
        context.update({
            'site_title': self.admin_site.site_title,
            'site_header': self.admin_site.site_header,
            'site_url': self.admin_site.site_url,
            'has_permission': self.admin_site.has_permission(self.request),
            'available_apps': self.admin_site.get_app_list(self.request),
        })
    

        return context

# Asegúrate de que esta parte esté en la clase BarberiaAdminSite
class BarberiaAdminSite(admin.AdminSite):
    site_header = "Administración de Barbería"
    site_title = "Panel de Barbería"
    index_title = "Dashboard de Gestión"
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('', self.admin_view(DashboardView.as_view()), name='index'),
        ]
        return self.get_custom_urls() + super().get_urls()
     
    def get_custom_urls(self):
        # Esta función se llamará desde get_urls
        return [
            path('', self.admin_view(DashboardView.as_view()), name='index'),
        ]
    
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        return app_list

# 2. Luego crea la instancia
barberia_admin_site = BarberiaAdminSite(name='barberia_admin')

# Registra los modelos con el site personalizado
barberia_admin_site.register(Cliente, ClienteAdmin)
barberia_admin_site.register(Empleado, EmpleadoAdmin)
barberia_admin_site.register(Servicio, ServicioAdmin)
barberia_admin_site.register(Cita, CitaAdmin)
barberia_admin_site.register(Producto, ProductoAdmin)
barberia_admin_site.register(Venta, VentaAdmin)
barberia_admin_site.register(MovimientoInventario, MovimientoInventarioAdmin)
barberia_admin_site.register(HorarioEmpleado, HorarioEmpleadoAdmin)
barberia_admin_site.register(Auditoria, AuditoriaAdmin)

# Importante: También registra los modelos de auth
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
barberia_admin_site.register(User, UserAdmin)
barberia_admin_site.register(Group, GroupAdmin)

class DashboardLinkMixin:
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        
        # Añadir un enlace al dashboard en el principio
        app_list.insert(0, {
            'name': 'Dashboard',
            'app_label': 'dashboard',
            'models': [{
                'name': 'Dashboard',
                'object_name': 'Dashboard',
                'admin_url': '/admin/',
                'view_only': True,
            }],
        })
        
        return app_list