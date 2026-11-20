# Recordatorios y confirmación de citas

BarberForge envía los recordatorios **por correo electrónico** de forma automática. No hay notificaciones push,
SMS ni WhatsApp por ahora.

## Recordatorio de confirmación (40 minutos antes)
- Lo reciben todas las citas **pendientes**, es decir, las agendadas por el cliente en la plataforma.
- El correo trae un **enlace para confirmar** la asistencia.
- Tienes **15 minutos** para confirmar. Si no confirmas, la cita **se cancela automáticamente** y la franja queda
  libre para otro cliente. No hay cobro.
- Las citas creadas por el barbero o el administrador en el local ya están confirmadas y no necesitan este correo.

## Aviso extra (60 minutos antes) para citas con riesgo alto de inasistencia
- Cuando agendas, un modelo de machine learning calcula la probabilidad de que la cita no se cumpla. Usa datos de la
  cita y del historial: día y hora, cuánta anticipación hubo al agendar, si el cliente es invitado o registrado,
  sus citas y faltas anteriores, el precio y el número de servicios.
- Si el riesgo es de **20 % o más**, recibes un **aviso 60 minutos antes** («Tu cita es en una hora») y después el
  recordatorio de confirmación de los 40 minutos. Es decir, **dos correos**.
- Si el riesgo es menor, solo recibes el recordatorio de 40 minutos.
- El aviso de 60 minutos no pide confirmar; solo te recuerda la cita.
- El cliente no ve su porcentaje de riesgo; solo lo ven el barbero y el administrador.

## Si no te llegan los correos
1. Revisa la carpeta de **spam** o **promociones**.
2. Verifica en **«Mi cuenta»** que tu correo esté bien escrito.
3. Si la cita se agendó en el local como invitado, el correo solo llega si diste uno.
4. Si el problema sigue, envía una PQRS al correo pqrs@barberforge.example.

## Confirmé tarde y la cita se canceló
Si pasaron los 15 minutos, la cita ya se canceló y la hora pudo tomarla otra persona. Agenda una nueva cita en la
plataforma.
