from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from .models import Cita, Venta, DetalleVenta, DetalleCita
from django.utils import timezone
from django.urls import path
@staff_member_required
def crear_venta_desde_cita(request, object_id):
    cita = get_object_or_404(Cita, pk=object_id)
    
    # Verificar que la cita no tenga una venta ya asociada
    try:
        venta_existente = Venta.objects.get(cita=cita)
        # Usa tu admin site personalizado si es necesario
        return redirect('barberia_admin:barberia_app_venta_change', venta_existente.pk)
    except Venta.DoesNotExist:
        pass
    
    # Crear la venta
    venta = Venta(
        cliente=cita.cliente,
        empleado=cita.empleado,
        cita=cita,
        fecha_hora=timezone.now(),
        subtotal=0,
        impuestos=0,
        descuentos=0,
        total=0,
        metodo_pago='efectivo',  # Valor predeterminado
        estado='completada'
    )
    venta.save()
    
    # Añadir servicios de la cita como detalles de venta
    subtotal = 0
    for detalle_cita in DetalleCita.objects.filter(cita=cita):
        detalle_venta = DetalleVenta(
            venta=venta,
            tipo='servicio',
            servicio=detalle_cita.servicio,
            cantidad=1,
            precio_unitario=detalle_cita.precio_aplicado,
            descuento_aplicado=0,
            subtotal_linea=detalle_cita.precio_aplicado
        )
        detalle_venta.save()
        subtotal += detalle_cita.precio_aplicado
    
    # Actualizar totales
    venta.subtotal = subtotal
    venta.total = subtotal + venta.impuestos - venta.descuentos
    venta.save()
    
    return redirect('admin:barberia_app_venta_change', venta.pk)

def get_urls(self):
    urls = super().get_urls()
    custom_urls = [
        path(
            '<path:object_id>/crear-venta/',  # Cambia object_id a cita_id
            self.admin_site.admin_view(crear_venta_desde_cita),
            name='crear_venta',
        ),
    ]
    return custom_urls + urls

