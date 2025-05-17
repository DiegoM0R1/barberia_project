from django.db import models

from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

# Helpers para choices de ENUMs
class EstadoEmpleado(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    INACTIVO = 'inactivo', 'Inactivo'
    VACACIONES = 'vacaciones', 'Vacaciones'

class EstadoCita(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    CONFIRMADA = 'confirmada', 'Confirmada'
    COMPLETADA = 'completada', 'Completada'
    CANCELADA = 'cancelada', 'Cancelada'
    NO_ASISTIO = 'no_asistio', 'No Asistió'

class MetodoPagoVenta(models.TextChoices):
    EFECTIVO = 'efectivo', 'Efectivo'
    TARJETA_CREDITO = 'tarjeta_credito', 'Tarjeta de Crédito'
    TARJETA_DEBITO = 'tarjeta_debito', 'Tarjeta de Débito'
    TRANSFERENCIA = 'transferencia', 'Transferencia'
    OTRO = 'otro', 'Otro'

class EstadoVenta(models.TextChoices):
    COMPLETADA = 'completada', 'Completada'
    ANULADA = 'anulada', 'Anulada'
    REEMBOLSADA = 'reembolsada', 'Reembolsada'

class TipoDetalleVenta(models.TextChoices):
    PRODUCTO = 'producto', 'Producto'
    SERVICIO = 'servicio', 'Servicio'

class TipoMovimientoInventario(models.TextChoices):
    ENTRADA = 'entrada', 'Entrada'
    SALIDA_VENTA = 'salida_venta', 'Salida por Venta'
    SALIDA_USO_INTERNO = 'salida_uso_interno', 'Salida por Uso Interno'
    AJUSTE_POSITIVO = 'ajuste_positivo', 'Ajuste Positivo'
    AJUSTE_NEGATIVO = 'ajuste_negativo', 'Ajuste Negativo'

class OperacionAuditoria(models.TextChoices):
    INSERT = 'INSERT', 'Inserción'
    UPDATE = 'UPDATE', 'Actualización'
    DELETE = 'DELETE', 'Eliminación'

class DiaSemana(models.IntegerChoices):
    LUNES = 1, 'Lunes'
    MARTES = 2, 'Martes'
    MIERCOLES = 3, 'Miércoles'
    JUEVES = 4, 'Jueves'
    VIERNES = 5, 'Viernes'
    SABADO = 6, 'Sábado'
    DOMINGO = 7, 'Domingo'


class Cliente(models.Model):
    cliente_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    telefono = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField(default=timezone.now)
    preferencias = models.TextField(blank=True, null=True, help_text='Ej: tipo de corte preferido, productos usados')
    historial_notas = models.TextField(blank=True, null=True)
    ultima_visita = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'clientes'
        indexes = [
            models.Index(fields=['nombre', 'apellido'], name='idx_cliente_nombre_apellido'),
        ]
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

class Empleado(models.Model):
    empleado_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    telefono = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    puesto = models.CharField(max_length=50, help_text='Ej: Barbero Principal, Barbero, Recepcionista')
    especialidad = models.CharField(max_length=100, blank=True, null=True, help_text='Ej: Cortes clásicos, Degradados, Afeitado con navaja')
    fecha_contratacion = models.DateField()
    porcentaje_comision = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    estado = models.CharField(
        max_length=20,
        choices=EstadoEmpleado.choices,
        default=EstadoEmpleado.ACTIVO
    )

    class Meta:
        db_table = 'empleados'
        indexes = [
            models.Index(fields=['nombre', 'apellido'], name='idx_empleado_nombre_apellido'),
            models.Index(fields=['especialidad'], name='idx_empleado_especialidad'),
        ]
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.puesto})"

class Servicio(models.Model):
    servicio_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    duracion_minutos = models.IntegerField(validators=[MinValueValidator(1)])
    precio = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    categoria = models.CharField(max_length=50, help_text='Ej: Cortes, Barba, Afeitado, Tratamientos')
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'servicios'
        indexes = [
            models.Index(fields=['categoria'], name='idx_servicio_categoria'),
            models.Index(fields=['activo'], name='idx_servicio_activo'),
        ]
        verbose_name = "Servicio"
        verbose_name_plural = "Servicios"

    def __str__(self):
        return f"{self.nombre} ({self.categoria})"

class Cita(models.Model):
    cita_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, db_column='cliente_id')
    empleado = models.ForeignKey(Empleado, on_delete=models.RESTRICT, db_column='empleado_id') # RESTRICT no es directamente soportado por Django a nivel de ORM, se maneja a nivel DB.
                                                                                             # En Django, on_delete=models.PROTECT es similar.
    fecha_hora = models.DateTimeField()
    duracion_total = models.IntegerField(help_text='Duración total calculada de los servicios en la cita') # Este campo se actualiza por el procedimiento almacenado sp_actualizar_duracion_cita
    estado = models.CharField(
        max_length=20,
        choices=EstadoCita.choices,
        default=EstadoCita.PENDIENTE
    )
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'citas'
        unique_together = (('empleado', 'fecha_hora'),) # Corresponde a uni_empleado_fecha_hora
        indexes = [
            models.Index(fields=['fecha_hora'], name='idx_cita_fecha_hora'),
            models.Index(fields=['empleado', 'fecha_hora'], name='idx_cita_empleado_fecha'),
            models.Index(fields=['cliente'], name='idx_cita_cliente'),
            models.Index(fields=['estado'], name='idx_cita_estado'),
        ]
        verbose_name = "Cita"
        verbose_name_plural = "Citas"

    def __str__(self):
        cliente_nombre = self.cliente.nombre if self.cliente else "Sin cliente"
        return f"Cita ID: {self.cita_id} - {cliente_nombre} con {self.empleado.nombre} el {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"

    # Nota: El trigger 'validate_cita_horario' se ejecuta a nivel de BD.
    # Para una validación a nivel de Django, se podría implementar un método clean() o signals.

class DetalleCita(models.Model):
    detalle_cita_id = models.AutoField(primary_key=True)
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, db_column='cita_id')
    servicio = models.ForeignKey(Servicio, on_delete=models.RESTRICT, db_column='servicio_id') # Similar a Cita.empleado, PROTECT en Django.
    precio_aplicado = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField()
    notas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'detalle_citas'
        unique_together = (('cita', 'servicio'),) # Corresponde a uni_cita_servicio
        indexes = [
            models.Index(fields=['servicio'], name='idx_detalle_cita_servicio'),
        ]
        verbose_name = "Detalle de Cita"
        verbose_name_plural = "Detalles de Citas"

    def __str__(self):
        return f"Detalle de Cita ID: {self.detalle_cita_id} - {self.servicio.nombre} para Cita {self.cita_id}"

    # Al guardar un DetalleCita, se debería llamar al procedimiento almacenado sp_actualizar_duracion_cita.
    # Esto se puede hacer con signals (post_save, post_delete) o sobrescribiendo el método save().
    # from django.db.models.signals import post_save, post_delete
    # from django.dispatch import receiver
    # from django.db import connection

    # @receiver([post_save, post_delete], sender=DetalleCita)
    # def actualizar_duracion_cita_signal(sender, instance, **kwargs):
    #     with connection.cursor() as cursor:
    #         cursor.callproc('sp_actualizar_duracion_cita', [instance.cita.cita_id])


class Producto(models.Model):
    producto_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    marca = models.CharField(max_length=50, blank=True, null=True)
    categoria = models.CharField(max_length=50, help_text='Ej: Ceras, Aceites para barba, Aftershaves, Champús para hombre')
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    precio_costo = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    stock_actual = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    stock_minimo = models.IntegerField(default=5, validators=[MinValueValidator(0)])
    unidad_medida = models.CharField(max_length=20, default='unidad')
    para_venta = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'productos'
        indexes = [
            models.Index(fields=['categoria'], name='idx_producto_categoria'),
            models.Index(fields=['marca'], name='idx_producto_marca'),
            # idx_producto_stock_bajo ((stock_actual <= stock_minimo)) es un índice funcional.
            # Django no lo crea directamente. Se puede crear manualmente en la BD o con una migración custom.
            models.Index(fields=['activo'], name='idx_producto_activo'),
        ]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.nombre} ({self.marca or 'Sin marca'}) - Stock: {self.stock_actual}"

class Venta(models.Model):
    venta_id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, db_column='cliente_id')
    empleado = models.ForeignKey(Empleado, on_delete=models.RESTRICT, db_column='empleado_id') # PROTECT en Django
    cita = models.OneToOneField(Cita, on_delete=models.SET_NULL, null=True, blank=True, db_column='cita_id') # UNIQUE a nivel de BD
    fecha_hora = models.DateTimeField(default=timezone.now)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descuentos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPagoVenta.choices
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoVenta.choices,
        default=EstadoVenta.COMPLETADA
    )
    notas = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'ventas'
        indexes = [
            models.Index(fields=['fecha_hora'], name='idx_venta_fecha'),
            models.Index(fields=['cliente'], name='idx_venta_cliente'),
            models.Index(fields=['empleado'], name='idx_venta_empleado'),
            models.Index(fields=['estado'], name='idx_venta_estado'),
        ]
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"

    def __str__(self):
        return f"Venta ID: {self.venta_id} - Total: {self.total} ({self.estado})"

class DetalleVenta(models.Model):
    detalle_venta_id = models.AutoField(primary_key=True)
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, db_column='venta_id')
    tipo = models.CharField(
        max_length=10,
        choices=TipoDetalleVenta.choices
    )
    producto = models.ForeignKey(Producto, on_delete=models.RESTRICT, null=True, blank=True, db_column='producto_id') # PROTECT
    servicio = models.ForeignKey(Servicio, on_delete=models.RESTRICT, null=True, blank=True, db_column='servicio_id') # PROTECT
    cantidad = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    subtotal_linea = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_ventas'
        indexes = [
            models.Index(fields=['producto'], name='idx_detalle_venta_producto'),
            models.Index(fields=['servicio'], name='idx_detalle_venta_servicio'),
        ]
        verbose_name = "Detalle de Venta"
        verbose_name_plural = "Detalles de Ventas"

    def clean(self):
        # Implementación del CHECK constraint de la BD
        # (tipo = 'producto' AND producto_id IS NOT NULL AND servicio_id IS NULL) OR
        # (tipo = 'servicio' AND servicio_id IS NOT NULL AND producto_id IS NULL)
        if self.tipo == TipoDetalleVenta.PRODUCTO:
            if not self.producto_id or self.servicio_id:
                raise models.ValidationError(
                    "Si el tipo es 'producto', producto_id debe tener valor y servicio_id debe ser nulo."
                )
        elif self.tipo == TipoDetalleVenta.SERVICIO:
            if not self.servicio_id or self.producto_id:
                raise models.ValidationError(
                    "Si el tipo es 'servicio', servicio_id debe tener valor y producto_id debe ser nulo."
                )
        super().clean()

    def __str__(self):
        item_nombre = self.producto.nombre if self.tipo == TipoDetalleVenta.PRODUCTO else self.servicio.nombre
        return f"Detalle Venta ID: {self.detalle_venta_id} - {self.tipo}: {item_nombre} x{self.cantidad}"

class MovimientoInventario(models.Model):
    movimiento_id = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.RESTRICT, db_column='producto_id') # PROTECT
    tipo_movimiento = models.CharField(
        max_length=30,
        choices=TipoMovimientoInventario.choices
    )
    cantidad = models.IntegerField() # Puede ser negativa para salidas si se modela así, pero el trigger ya maneja la lógica de +/-
    fecha_hora = models.DateTimeField(default=timezone.now)
    empleado = models.ForeignKey(Empleado, on_delete=models.SET_NULL, null=True, blank=True, db_column='empleado_id')
    venta = models.ForeignKey(Venta, on_delete=models.SET_NULL, null=True, blank=True, db_column='venta_id')
    motivo = models.CharField(max_length=255, blank=True, null=True)
    documento_referencia = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'movimientos_inventario'
        indexes = [
            models.Index(fields=['producto'], name='idx_movimiento_producto'),
            models.Index(fields=['fecha_hora'], name='idx_movimiento_fecha'),
            models.Index(fields=['tipo_movimiento'], name='idx_movimiento_tipo'),
        ]
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self):
        return f"Movimiento ID: {self.movimiento_id} - {self.producto.nombre} ({self.tipo_movimiento}: {self.cantidad})"
    
    # Nota: El trigger 'update_stock_after_movement' actualiza productos.stock_actual automáticamente
    # al insertar un MovimientoInventario.

class HorarioEmpleado(models.Model):
    horario_id = models.AutoField(primary_key=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, db_column='empleado_id')
    dia_semana = models.IntegerField(
        choices=DiaSemana.choices,
        help_text='1=Lunes, ..., 7=Domingo'
    )
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    es_descanso = models.BooleanField(default=False)

    class Meta:
        db_table = 'horarios_empleados'
        indexes = [
            models.Index(fields=['empleado', 'dia_semana'], name='idx_horario_empleado_dia'),
        ]
        # CHECK (hora_inicio < hora_fin OR (hora_inicio = '00:00:00' AND hora_fin = '23:59:59' AND es_descanso = TRUE))
        # CHECK (dia_semana BETWEEN 1 AND 7) -> Cubierto por choices
        # Estas validaciones CHECK más complejas se pueden añadir en un método clean() del modelo.
        verbose_name = "Horario de Empleado"
        verbose_name_plural = "Horarios de Empleados"

    def clean(self):
        if not self.es_descanso and self.hora_inicio >= self.hora_fin:
            raise models.ValidationError("La hora de inicio debe ser menor que la hora de fin para horarios de trabajo.")
        if self.es_descanso and not (self.hora_inicio == timezone.datetime.min.time() and self.hora_fin == timezone.datetime.max.time().replace(microsecond=0)):
             if self.hora_inicio >= self.hora_fin: # Si es un descanso parcial, también debe tener coherencia
                raise models.ValidationError("Para descansos parciales, la hora de inicio debe ser menor que la hora de fin.")
        super().clean()

    def __str__(self):
        return f"Horario de {self.empleado.nombre}: {self.get_dia_semana_display()} de {self.hora_inicio} a {self.hora_fin}"

class Auditoria(models.Model):
    log_id = models.BigAutoField(primary_key=True)
    tabla_afectada = models.CharField(max_length=64)
    operacion = models.CharField(
        max_length=10,
        choices=OperacionAuditoria.choices
    )
    registro_id = models.CharField(max_length=255) # ID del registro afectado, puede ser string si es UUID, etc.
    datos_antiguos = models.JSONField(null=True, blank=True)
    datos_nuevos = models.JSONField(null=True, blank=True)
    usuario_db = models.CharField(max_length=100)
    usuario_app = models.CharField(max_length=100, null=True, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now) # El (6) de DATETIME(6) es para microsegundos, Django lo maneja.
    ip_origen = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        db_table = 'auditoria'
        indexes = [
            models.Index(fields=['fecha_hora'], name='idx_auditoria_fecha'),
            models.Index(fields=['tabla_afectada'], name='idx_auditoria_tabla'),
        ]
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"

    def __str__(self):
        return f"Log ID: {self.log_id} - {self.operacion} en {self.tabla_afectada} ({self.fecha_hora})"

# Vistas SQL como modelos no gestionados (solo lectura)
# class VistaDisponibilidadEmpleados(models.Model):
#     empleado_id = models.IntegerField(primary_key=True) # Necesita una clave primaria para Django
#     empleado_nombre = models.CharField(max_length=101)
#     puesto = models.CharField(max_length=50)
#     especialidad = models.CharField(max_length=100, null=True, blank=True)
#     dia_semana = models.SmallIntegerField()
#     nombre_dia = models.CharField(max_length=10)
#     hora_inicio = models.TimeField()
#     hora_fin = models.TimeField()
#     es_descanso = models.BooleanField()

#     class Meta:
#         managed = False # Django no creará ni modificará esta tabla/vista
#         db_table = 'v_disponibilidad_empleados'
#         verbose_name = "Disponibilidad de Empleado (Vista)"
#         verbose_name_plural = "Disponibilidades de Empleados (Vista)"

# class VistaProximasCitas(models.Model):
#     cita_id = models.IntegerField(primary_key=True) # Necesita una clave primaria
#     fecha_hora = models.DateTimeField()
#     cliente_nombre = models.CharField(max_length=101, null=True, blank=True)
#     cliente_telefono = models.CharField(max_length=15, null=True, blank=True)
#     barbero_nombre = models.CharField(max_length=101)
#     duracion_cita_minutos = models.IntegerField()
#     estado_cita = models.CharField(max_length=20)
#     servicios_programados = models.TextField(null=True, blank=True)
#     notas_cita = models.TextField(null=True, blank=True)

#     class Meta:
#         managed = False
#         db_table = 'v_proximas_citas'
#         verbose_name = "Próxima Cita (Vista)"
#         verbose_name_plural = "Próximas Citas (Vista)"


