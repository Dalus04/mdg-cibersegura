import json

from sqlalchemy import select

from app.extensions import db
from app.models import (
    Actividad,
    Alternativa,
    Contenido,
    Evaluacion,
    Pregunta,
    Tema,
)

DATOS_TEMAS_INICIALES = [
    {
        "titulo": "Gestión de contraseñas seguras y autenticación",
        "descripcion": (
            "Aprende a crear claves robustas, evitar patrones predecibles y utilizar "
            "la autenticación en dos pasos para proteger tus cuentas personales e institucionales."
        ),
        "orden": 1,
        "contenidos": [
            {
                "titulo": "¿Por qué una contraseña débil pone en riesgo tus cuentas?",
                "orden": 1,
                "contenido": (
                    "Muchos incidentes de seguridad digital ocurren por el uso de contraseñas fáciles de adivinar "
                    "o por reutilizar la misma clave en múltiples servicios (redes sociales, correo, cuentas bancarias).\n\n"
                    "Los atacantes utilizan programas automatizados capaces de probar millones de combinaciones comunes por segundo "
                    "(ataques de fuerza bruta y diccionario). Si utilizas secuencias como '123456', nombres de familiares o fechas de nacimiento, "
                    "un intruso puede vulnerar tu cuenta en cuestión de segundos.\n\n"
                    "Riesgos principales:\n"
                    "• Efecto dominó: si vulneran una cuenta, pueden intentar la misma clave en tus otros servicios.\n"
                    "• Pérdida de identidad digital y acceso a comunicaciones personales.\n"
                    "• Acceso a información financiera o confidencial."
                ),
            },
            {
                "titulo": "Buenas prácticas para contraseñas robustas y memorables",
                "orden": 2,
                "contenido": (
                    "Una contraseña segura no tiene que ser imposible de recordar. Una de las técnicas más efectivas es utilizar "
                    "una frase de contraseña ('passphrase') compuesta por cuatro o más palabras no relacionadas entre sí.\n\n"
                    "Recomendaciones clave:\n"
                    "1. Longitud: utiliza al menos 12 a 16 caracteres. La longitud suele ser más determinante que la complejidad.\n"
                    "2. Variedad: combina letras mayúsculas, minúsculas, números y símbolos.\n"
                    "3. Unicidad: ten una contraseña distinta para cada servicio crítico.\n"
                    "4. Gestores de contraseñas: considera usar un gestor seguro para no tener que memorizarlas todas ni anotarlas en lugares visibles."
                ),
            },
            {
                "titulo": "Autenticación en dos pasos (2FA): la segunda barrera defensiva",
                "orden": 3,
                "contenido": (
                    "La autenticación en dos pasos (2FA o MFA) añade una capa adicional de protección: requiere algo que sabes "
                    "(tu contraseña) y algo que tienes (un código generado en tu teléfono móvil o una llave de seguridad física).\n\n"
                    "¿Cómo te protege?\n"
                    "Incluso si un atacante descubre o filtra tu contraseña, no podrá acceder a tu cuenta sin el segundo factor de autenticación.\n\n"
                    "Se recomienda activar 2FA de forma prioritaria en:\n"
                    "• Correo electrónico principal (que suele ser la llave de recuperación de otros servicios).\n"
                    "• Aplicaciones financieras y bancarias.\n"
                    "• Redes sociales y mensajería instantánea."
                ),
            },
        ],
    },
    {
        "titulo": "Detección de enlaces fraudulentos y phishing",
        "descripcion": (
            "Identifica correos engañosos, mensajes de texto fraudulentos (smishing) y sitios web falsos "
            "que buscan suplantar identidades para robar credenciales y dinero."
        ),
        "orden": 2,
        "contenidos": [
            {
                "titulo": "¿Qué es el phishing y cómo identificarlo?",
                "orden": 1,
                "contenido": (
                    "El phishing es una técnica de ingeniería social en la que ciberdelincuentes se hacen pasar por entidades de confianza "
                    "(como bancos, municipalidades, servicios de entrega o empresas de telefonía) para manipularte y lograr que reveles información confidencial.\n\n"
                    "Suele presentarse a través de:\n"
                    "• Correos electrónicos con logotipos casi idénticos a los originales.\n"
                    "• Mensajes SMS con enlaces alarmistas sobre transferencias bloqueadas o multas urgentes.\n"
                    "• Mensajes de WhatsApp prometiendo bonos o beneficios estatales condicionados a hacer clic en un enlace."
                ),
            },
            {
                "titulo": "Señales de alerta en mensajes digitales sospechosos",
                "orden": 2,
                "contenido": (
                    "Presta atención a las siguientes señales frecuentes de engaño:\n\n"
                    "1. Sensación de extrema urgencia: frases como '¡Acción inmediata requerida!', 'Tu cuenta será suspendida en 24 horas'.\n"
                    "2. Remitentes no oficiales: revisa la dirección de correo real después del '@'. Los bancos o instituciones oficiales no usan dominios públicos (gmail.com, hotmail.com) ni dominios con pequeñas variaciones tipográficas.\n"
                    "3. Solicitud de información confidencial: ninguna entidad seria te pedirá por correo o mensaje tu clave secreta o token digital.\n"
                    "4. Enlaces acortados o sospechosos que no muestran el destino real."
                ),
            },
            {
                "titulo": "Cómo inspeccionar un enlace antes de interactuar",
                "orden": 3,
                "contenido": (
                    "Antes de pulsar un enlace, sigue estos pasos defensivos:\n\n"
                    "• En computadora: pasa el cursor sobre el enlace sin hacer clic para ver la URL real en la esquina inferior del navegador.\n"
                    "• En dispositivos móviles: mantén presionado el enlace con precaución para previsualizar la dirección de destino.\n"
                    "• Recuerda: el candado verde o HTTPS indica únicamente que la conexión está cifrada, pero no garantiza que el sitio sea legítimo.\n"
                    "• Si tienes dudas, ingresa escribiendo la dirección oficial directamente en tu navegador o comunícate por los canales telefónicos oficiales."
                ),
            },
        ],
    },
    {
        "titulo": "Protección de datos personales y privacidad digital",
        "descripcion": (
            "Conoce la importancia de proteger tus datos personales conforme al marco normativo "
            "y aprende a minimizar tu huella digital frente a terceros."
        ),
        "orden": 3,
        "contenidos": [
            {
                "titulo": "Tus datos personales y la Ley N.° 29733",
                "orden": 1,
                "contenido": (
                    "En el Perú, la Ley N.° 29733 (Ley de Protección de Datos Personales) garantiza que tu información personal "
                    "(nombres, DNI, dirección, teléfono, huellas, imágenes) debe ser tratada con tu consentimiento informado y para fines legítimos.\n\n"
                    "Como ciudadano tienes derecho a:\n"
                    "• Conocer qué datos tuyos almacena una entidad.\n"
                    "• Solicitar la rectificación de datos inexactos.\n"
                    "• Pedir la cancelación o supresión cuando ya no sean necesarios para la finalidad autorizada."
                ),
            },
            {
                "titulo": "Minimización de datos y huella digital",
                "orden": 2,
                "contenido": (
                    "Cada vez que te registras en un portal, realizas una publicación o aceptas permisos en tu celular, dejas un rastro llamado 'huella digital'.\n\n"
                    "Recomendaciones para proteger tu privacidad:\n"
                    "• Principio de minimización: brinda únicamente los datos estrictamente necesarios para el trámite o servicio.\n"
                    "• No compartas públicamente fotografías de documentos de identidad, pasajes con códigos QR o recibos de servicios.\n"
                    "• Revisa periódicamente los permisos que otorgas a las aplicaciones móviles (micrófono, cámara, ubicación y contactos)."
                ),
            },
        ],
    },
    {
        "titulo": "Navegación segura y redes Wi-Fi públicas",
        "descripcion": (
            "Prácticas seguras para navegar en internet desde el hogar, el trabajo o redes inalámbricas abiertas."
        ),
        "orden": 4,
        "contenidos": [
            {
                "titulo": "Riesgos al conectarse a redes Wi-Fi públicas abiertas",
                "orden": 1,
                "contenido": (
                    "Las redes Wi-Fi abiertas en plazas públicas, centros comerciales o cafeterías suelen carecer de mecanismos "
                    "de cifrado robustos entre los dispositivos conectados.\n\n"
                    "Esto permite que un atacante conectado a la misma red pueda interceptar comunicaciones no cifradas, "
                    "o incluso montar una red falsa con el mismo nombre para capturar contraseñas.\n\n"
                    "Regla de oro: en redes públicas, jamás realices transferencias bancarias ni accedas a servicios donde debas ingresar credenciales sensibles."
                ),
            },
            {
                "titulo": "Consejos para una navegación web protegida",
                "orden": 2,
                "contenido": (
                    "Para mantenerte seguro mientras exploras la web:\n\n"
                    "1. Mantén tu navegador y sistema operativo actualizados para contar con los últimos parches de seguridad.\n"
                    "2. Evita descargar archivos o programas desde sitios web no oficiales o de dudosa procedencia.\n"
                    "3. Presta atención a las advertencias del navegador cuando señale que un certificado digital ha caducado o es inválido.\n"
                    "4. Cierra sesión en computadoras compartidas o de acceso público al terminar tus actividades."
                ),
            },
        ],
    },
    {
        "titulo": "Seguridad en Compras Online y Billeteras Digitales (Yape/Plin)",
        "descripcion": (
            "Aprende a verificar tiendas virtuales, evitar comprobantes falsos en billeteras digitales y proteger tus tarjetas bancarias."
        ),
        "orden": 5,
        "contenidos": [
            {
                "titulo": "Prevención de capturas y comprobantes falsos en Yape y Plin",
                "orden": 1,
                "contenido": (
                    "Las billeteras digitales son muy populares en comercios locales, pero los delincuentes suelen utilizar aplicaciones simuladoras o capturas modadas para fingir pagos.\n\n"
                    "Regla de oro: Nunca te confíes de la imagen que te muestra el comprador en su celular. Revisa siempre el saldo y la notificación directamente en tu propia aplicación oficial antes de entregar un producto o servicio.\n\n"
                    "Desconfía de supuestos mensajes de texto (SMS) o correos que afirman que recibiste un abono."
                ),
            },
            {
                "titulo": "Verificación de tiendas virtuales y compras seguras",
                "orden": 2,
                "contenido": (
                    "Antes de realizar una compra por internet o redes sociales:\n\n"
                    "1. Verifica que la página web tenga el candado de seguridad (HTTPS) y una dirección URL correcta.\n"
                    "2. Investiga la reputación del vendedor, comentarios de otros usuarios y la antigüedad de la página.\n"
                    "3. Desconfía de precios exageradamente bajos u 'ofertas relámpago' que te presionen a transferir dinero rápidamente."
                ),
            },
            {
                "titulo": "Uso seguro de tarjetas de débito y crédito",
                "orden": 3,
                "contenido": (
                    "Para evitar la clonación o compras no autorizadas:\n\n"
                    "- Utiliza tarjetas virtuales con límite diario o tarjetas de crédito antes que la tarjeta de débito donde guardas tus ahorros principales.\n"
                    "- En tiendas físicas, jamás pierdas de vista tu tarjeta ni entregues el código CVV (los 3 dígitos al reverso).\n"
                    "- Activa en la aplicación de tu banco la opción de requerir clave o huella para compras por internet."
                ),
            },
            {
                "titulo": "Qué hacer si fuiste víctima de un fraude en línea",
                "orden": 4,
                "contenido": (
                    "Si realizaste un pago y no recibiste el producto o sospechas de una estafa:\n\n"
                    "1. Bloquea tu tarjeta o cuenta bancaria inmediatamente desde la app de tu banco o por vía telefónica.\n"
                    "2. Guarda todas las evidencias: capturas de chat, números de teléfono, vouchers y enlaces.\n"
                    "3. Presenta la denuncia correspondiente ante la Policía Nacional (Divindat) o la comisaría de tu distrito."
                ),
            },
        ],
    },
    {
        "titulo": "Ingeniería Social y Llamadas Extorsivas",
        "descripcion": (
            "Estrategias para identificar manipulación psicológica, responder ante llamadas de extorsión y evitar engaños por mensajes."
        ),
        "orden": 6,
        "contenidos": [
            {
                "titulo": "Análisis de la ingeniería social y la manipulación psicológica",
                "orden": 1,
                "contenido": (
                    "La ingeniería social es la técnica de manipular a las personas para que entreguen voluntariamente información confidencial o dinero.\n\n"
                    "Los atacantes utilizan dos emociones principales: el MIEDO (miedo a perder una cuenta, ser detenido) y la CODICIA (ganar un premio fácil o un bono del estado).\n\n"
                    "Si un mensaje o llamada te genera pánico o mucha emoción, detente a pensar antes de actuar."
                ),
            },
            {
                "titulo": "Protocolo frente a llamadas extorsivas y falsas emergencias (Vishing)",
                "orden": 2,
                "contenido": (
                    "Las llamadas extorsivas buscan perturbar tu tranquilidad con gritos o falsas acusaciones.\n\n"
                    "Pasos de acción inmediata:\n"
                    "1. MANTÉN LA CALMA y no entregues nombres de familiares ni información personal.\n"
                    "2. CUELGA DE INMEDIATO. No entables discusión con el extorsionador.\n"
                    "3. VERIFICA la situación llamando directamente al familiar presuntamente afectado o al banco correspondiente."
                ),
            },
            {
                "titulo": "Mensajes engañosos por SMS y WhatsApp (Smishing)",
                "orden": 3,
                "contenido": (
                    "Los delincuentes envían mensajes masivos anunciando 'paquetes retenidos', 'bonos del gobierno' o 'cuentas suspendidas'.\n\n"
                    "Recomendaciones clave:\n"
                    "- Nunca hagas clic en enlaces acortados o sospechosos.\n"
                    "- Las entidades oficiales y bancos nunca solicitan contraseñas o claves dinámicas por WhatsApp o SMS.\n"
                    "- Bloquea y reporta el número sospechoso."
                ),
            },
            {
                "titulo": "Medidas de seguridad en WhatsApp y canales de comunicación",
                "orden": 4,
                "contenido": (
                    "Para evitar que secuestren tu cuenta de WhatsApp y suplanten tu identidad:\n\n"
                    "1. Activa la 'Verificación en dos pasos' desde los ajustes de la aplicación e ingresa un PIN de 6 dígitos.\n"
                    "2. Configura tu foto de perfil para que solo sea visible por tus contactos guardados.\n"
                    "3. Jamás compartas el código de 6 dígitos que te llega por SMS al intentar registrar la app."
                ),
            },
        ],
    },
    {
        "titulo": "Uso Seguro de Inteligencia Artificial y Deepfakes",
        "descripcion": (
            "Comprende los riesgos de la clonación de voz, generación de contenidos falsos y cómo proteger tu privacidad al usar herramientas de IA."
        ),
        "orden": 7,
        "contenidos": [
            {
                "titulo": "Clonación de voz y videos falsos (Deepfakes)",
                "orden": 1,
                "contenido": (
                    "Hoy en día, herramientas de Inteligencia Artificial pueden clonar la voz de una persona con solo unos segundos de audio extraídos de sus redes sociales.\n\n"
                    "Cómo detectarlo:\n"
                    "- Escucha con atención: las voces clonadas a veces carecen de pausas naturales de respiración o entonación emocional adecuada.\n"
                    "- En videollamadas, observa si hay parpadeos anormales, bordes borrosos alrededor del rostro o descoordinación al hablar."
                ),
            },
            {
                "titulo": "Creación de un 'Código Familiar' para emergencias",
                "orden": 2,
                "contenido": (
                    "Ante la amenaza de la clonación de voz por IA, la mejor defensa comunitaria es la prevención familiar.\n\n"
                    "Acuerda con tu familia una 'Palabra Clave' o frase secreta que solo ustedes conozcan. Si alguien llama afirmando ser un familiar en apuros, pídeles que te diga la palabra clave para validar su identidad."
                ),
            },
            {
                "titulo": "Privacidad de datos personales al usar chatbots e IA",
                "orden": 3,
                "contenido": (
                    "Al utilizar chatbots o generadores de texto e imágenes en línea:\n\n"
                    "1. Evita ingresar nombres completos, números de DNI, dirección, fotos privadas o documentos institucionales.\n"
                    "2. Las conversaciones en plataformas públicas pueden ser almacenadas y utilizadas para entrenar futuros modelos.\n"
                    "3. Revisa los términos de privacidad antes de subir fotografías a aplicaciones de retoque por IA."
                ),
            },
            {
                "titulo": "Verificación de noticias falsas y contenidos manipulados por IA",
                "orden": 4,
                "contenido": (
                    "La IA facilita la creación rápida de noticias o comunicados falsos atribuibles a autoridades o instituciones.\n\n"
                    "- No reenvíes información alarmista sin antes consultar las fuentes u canales oficiales de la Municipalidad u organismo correspondiente.\n"
                    "- Utiliza herramientas de búsqueda inversa de imágenes para verificar si una foto es real o generada por computadora."
                ),
            },
        ],
    },
    {
        "titulo": "Seguridad Familiar y Control Parental",
        "descripcion": (
            "Guía práctica para proteger a niños, adolescentes y adultos mayores en el entorno digital, configurando filtros y acompañamiento."
        ),
        "orden": 8,
        "contenidos": [
            {
                "titulo": "Protección de niños y adolescentes frente a riesgos en línea",
                "orden": 1,
                "contenido": (
                    "Los menores están expuestos a ciberbullying, exposición a contenidos no aptos y acoso por parte de adultos (Grooming).\n\n"
                    "Buenas prácticas de prevención:\n"
                    "- Fomenta la confianza para que te cuenten sobre sus interacciones y amistades virtuales.\n"
                    "- Enseña a los niños a nunca compartir fotos vistiendo el uniforme escolar, su ubicación en tiempo real ni datos del hogar."
                ),
            },
            {
                "titulo": "Herramientas de Control Parental y gestión de tiempo",
                "orden": 2,
                "contenido": (
                    "Configurar límites en los dispositivos de los niños ayuda a mantener un uso equilibrado y seguro:\n\n"
                    "1. Utiliza aplicaciones gratuitas como Google Family Link para gestionar el tiempo de pantalla y aprobar descargas.\n"
                    "2. Activa el 'Modo Restringido' o 'Búsqueda Segura' (SafeSearch) en Google y YouTube.\n"
                    "3. Mantén las computadoras y consolas en áreas comunes de la casa."
                ),
            },
            {
                "titulo": "Acompañamiento y alfabetización digital para adultos mayores",
                "orden": 3,
                "contenido": (
                    "Los adultos mayores son un blanco frecuente para estafadores por su menor familiaridad con la tecnología.\n\n"
                    "Estrategias de apoyo:\n"
                    "- Configura la autenticación en dos pasos en sus correos y redes sociales.\n"
                    "- Explícales detenidamente que ningún banco solicitará sus claves secretas o token por llamada telefónica.\n"
                    "- Ayúdales a identificar mensajes fraudulentos antes de que realicen cualquier clic o llamada."
                ),
            },
        ],
    },
]


def seed_contenidos_iniciales() -> None:
    """Inserta temas y contenidos iniciales de forma idempotente."""
    for data_tema in DATOS_TEMAS_INICIALES:
        tema = db.session.scalar(
            select(Tema).where(Tema.titulo == data_tema["titulo"])
        )
        if tema is None:
            tema = Tema(
                titulo=data_tema["titulo"],
                descripcion=data_tema["descripcion"],
                orden=data_tema["orden"],
                estado="publicado",
            )
            db.session.add(tema)
            db.session.flush()

        titulos_existentes = {
            c.titulo
            for c in db.session.scalars(
                select(Contenido).where(Contenido.id_tema == tema.id_tema)
            ).all()
        }

        for data_contenido in data_tema["contenidos"]:
            if data_contenido["titulo"] not in titulos_existentes:
                contenido = Contenido(
                    id_tema=tema.id_tema,
                    titulo=data_contenido["titulo"],
                    contenido=data_contenido["contenido"],
                    orden=data_contenido["orden"],
                    estado="publicado",
                )
                db.session.add(contenido)

    db.session.commit()


USUARIOS_INICIALES = [
    {
        "nombres": "Administrador",
        "apellidos": "Municipal",
        "correo": "admin@guadalupe.gob.pe",
        "password": "Admin1234!",
        "rol_nombre": "administrador",
    },
    {
        "nombres": "Ciudadano",
        "apellidos": "Ejemplo",
        "correo": "ciudadano@ejemplo.com",
        "password": "Ciudadano123!",
        "rol_nombre": "ciudadano",
    },
]


def seed_usuarios_iniciales() -> None:
    """Inserta usuarios semilla para cada rol de forma idempotente."""
    from app.models import Rol, Usuario

    roles = {rol.nombre: rol for rol in db.session.scalars(select(Rol)).all()}

    for data in USUARIOS_INICIALES:
        correo_norm = Usuario.normalizar_correo(data["correo"])
        usuario = db.session.scalar(
            select(Usuario).where(Usuario.correo == correo_norm)
        )
        if usuario is None:
            rol = roles.get(data["rol_nombre"])
            if rol:
                nuevo_usuario = Usuario(
                    id_rol=rol.id_rol,
                    nombres=data["nombres"],
                    apellidos=data["apellidos"],
                    correo=correo_norm,
                    estado="activo",
                )
                nuevo_usuario.set_password(data["password"])
                db.session.add(nuevo_usuario)

    db.session.commit()


ACTIVIDADES_INICIALES = [
    {
        "tema_orden": 1,
        "titulo": "Taller interactivo: Creación y validación de Passphrase",
        "tipo": "practica",
        "instrucciones": json.dumps(
            {
                "introduccion": (
                    "En esta práctica interactiva aplicarás las recomendaciones aprendidas para crear "
                    "contraseñas seguras y comprenderás por qué la longitud supera a la complejidad simple."
                ),
                "caso_contexto": (
                    "Una vecina de Guadalupe necesita crear una contraseña para su cuenta de correo "
                    "y su banca digital. Desea una clave que sea resistente a ataques automatizados "
                    "de fuerza bruta y diccionario, pero que pueda memorizar sin anotarla en un papel."
                ),
                "pregunta": "¿Cuál de las siguientes propuestas de contraseña es la más segura y recomendable?",
                "opciones": [
                    {
                        "id": "opt_1",
                        "texto": "Guadalupe2026!",
                        "es_correcta": False,
                        "explicacion": (
                            "Incorrecta. Aunque incluye mayúscula, números y un símbolo, está formada "
                            "por una palabra común predecible (el nombre del distrito) y el año actual. "
                            "Los programas de ataque prueban estos patrones en cuestión de segundos."
                        ),
                    },
                    {
                        "id": "opt_2",
                        "texto": "P4$$w0rd#99",
                        "es_correcta": False,
                        "explicacion": (
                            "Incorrecta. Las sustituciones simples (como '4' por 'a' o '$' por 's') "
                            "están incorporadas en todos los diccionarios de cracking actuales y no "
                            "añaden seguridad real si la longitud es corta (11 caracteres)."
                        ),
                    },
                    {
                        "id": "opt_3",
                        "texto": "algarrobo-guitarra-rio-playa",
                        "es_correcta": True,
                        "explicacion": (
                            "¡Correcto! Esta frase de contraseña ('passphrase') tiene 28 caracteres "
                            "formados por cuatro palabras cotidianas no relacionadas. Su gran longitud "
                            "hace matemáticamente inviable un ataque de fuerza bruta moderno, y a la vez "
                            "es sumamente fácil de recordar."
                        ),
                    },
                ],
                "consejo_final": (
                    "Recuerda: la longitud (16 caracteres o más) y la unicidad de tu clave son tus mejores escudos. "
                    "Complementa siempre tus cuentas principales activando la autenticación en dos pasos (2FA)."
                ),
            },
            ensure_ascii=False,
        ),
    },
    {
        "tema_orden": 2,
        "titulo": "Simulador de Alerta: Detección de Mensaje de Phishing Bancario",
        "tipo": "simulacion",
        "instrucciones": json.dumps(
            {
                "introduccion": (
                    "Entorno seguro de simulación de ciberseguridad. Examina con atención el siguiente "
                    "correo electrónico sospechoso simulado y toma la decisión más prudente."
                ),
                "escenario_simulado": {
                    "tipo_mensaje": "Correo electrónico",
                    "remitente_nombre": "Banco de la Nación - Notificaciones Oficiales",
                    "remitente_direccion": "alerta-seguridad@bn-verificacion-urgente.net",
                    "destinatario": "ciudadano.guadalupe@ejemplo.com",
                    "asunto": "🚨 URGENTE: Bloqueo preventivo de su tarjeta y banca por internet en 2 horas",
                    "fecha": "Hoy, 09:30 AM",
                    "mensaje": (
                        "Estimado(a) ciudadano(a):\n\n"
                        "Detectamos múltiples intentos de acceso no autorizados a su cuenta desde una ubicación no habitual.\n\n"
                        "Por protocolo de seguridad institucional, sus operaciones electrónicas y tarjetas serán SUSPENDIDAS "
                        "en un plazo máximo de 2 HORAS salvo que valide su identidad de inmediato a través de nuestro enlace oficial:\n\n"
                        "👉 http://bn-verificacion-urgente.net/actualizar-datos-login\n\n"
                        "Si no actualiza sus credenciales dentro del plazo, su cuenta quedará bloqueada indefinidamente.\n\n"
                        "Atentamente,\n"
                        "División de Prevención de Fraudes"
                    ),
                    "enlace_falso": "http://bn-verificacion-urgente.net/actualizar-datos-login",
                },
                "indicios_analisis": [
                    {
                        "elemento": "Dominio falso del remitente",
                        "descripcion": "El correo proviene de '@bn-verificacion-urgente.net' en lugar del dominio oficial del Estado (.gob.pe o .com.pe).",
                    },
                    {
                        "elemento": "Sentido falso de extrema urgencia",
                        "descripcion": "Amenaza con bloqueo en 2 horas para forzar una decisión impulsiva sin verificar.",
                    },
                    {
                        "elemento": "Enlace fraudulento",
                        "descripcion": "Usa HTTP no seguro y conduce a un sitio web falso diseñado para clonar tus claves.",
                    },
                ],
                "pregunta": "¿Qué acción debes tomar ante este mensaje?",
                "opciones": [
                    {
                        "id": "opt_hacer_clic",
                        "texto": "Hacer clic en el enlace de inmediato e ingresar mi documento y clave para que no me bloqueen.",
                        "es_correcta": False,
                        "explicacion": (
                            "🚨 ¡PELIGRO! Habrías caído en la trampa del atacante. La página clonada robaría "
                            "tu número de tarjeta y clave secreta, permitiendo a los delincuentes vaciar tus fondos."
                        ),
                    },
                    {
                        "id": "opt_responder",
                        "texto": "Responder al correo adjuntando una foto de mi DNI para demostrar que soy el titular.",
                        "es_correcta": False,
                        "explicacion": (
                            "⚠️ RIESGO GRAVE. Estarías entregando tus datos personales sensibles directamente "
                            "a ciberdelincuentes, facilitando la suplantación de tu identidad y fraudes crediticios."
                        ),
                    },
                    {
                        "id": "opt_identificar_phishing",
                        "texto": "Identificar el correo como Phishing: no abrir el enlace, no responder y verificar directamente por canales oficiales o presenciales.",
                        "es_correcta": True,
                        "explicacion": (
                            "🛡️ ¡DECISIÓN CORRECTA! Reconociste las señales de alarma: remitente falso, "
                            "urgencia extorsiva y enlace fraudulento. Ninguna institución oficial o banco "
                            "solicita claves ni actualiza datos por enlaces directos de correo."
                        ),
                    },
                ],
                "consejo_final": (
                    "Ante cualquier notificación de 'bloqueo urgente', nunca utilices los enlaces del mensaje. "
                    "Comunícate siempre por los números telefónicos oficiales que figuran al dorso de tu tarjeta o acude a la agencia."
                ),
            },
            ensure_ascii=False,
        ),
    },
    {
        "tema_orden": 3,
        "titulo": "Simulador de Privacidad: Permisos Excesivos en Aplicaciones Móviles",
        "tipo": "simulacion",
        "instrucciones": json.dumps(
            {
                "introduccion": (
                    "Aprende a proteger tus datos personales conforme a los principios de proporcionalidad "
                    "y finalidad establecidos en la Ley N.° 29733 de Protección de Datos Personales."
                ),
                "caso_contexto": (
                    "Instalas una aplicación gratuita llamada 'Linterna Brillante HD' en tu teléfono celular. "
                    "Al iniciarla por primera vez, te solicita los siguientes permisos en pantalla:\n\n"
                    "• Cámara y Flash (requerido para encender la luz)\n"
                    "• Acceso a toda tu libreta de Contactos\n"
                    "• Ubicación GPS precisa en tiempo real\n"
                    "• Acceso permanente al Micrófono"
                ),
                "pregunta": "¿Cuál es la conducta más adecuada respetando tu privacidad digital?",
                "opciones": [
                    {
                        "id": "opt_aceptar_todo",
                        "texto": "Aceptar todos los permisos sin leer para que la aplicación funcione más rápido.",
                        "es_correcta": False,
                        "explicacion": (
                            "Riesgo alto: La aplicación recopilará tus contactos personales, ubicación y audios "
                            "para venderlos a terceros o realizar perfiles publicitarios invasivos sin tu consentimiento informado."
                        ),
                    },
                    {
                        "id": "opt_limitar_permisos",
                        "texto": "Conceder únicamente el permiso de Flash/Cámara (estrictamente necesario) y denegar Contactos, Ubicación y Micrófono.",
                        "es_correcta": True,
                        "explicacion": (
                            "¡Excelente! Aplicas el principio de proporcionalidad (Ley 29733): una herramienta "
                            "solo debe tener acceso a los datos indispensables para su finalidad técnica."
                        ),
                    },
                    {
                        "id": "opt_desinstalar",
                        "texto": "Denegar los permisos invasivos y desinstalar la app, buscando una alternativa que no pida datos desmedidos.",
                        "es_correcta": True,
                        "explicacion": (
                            "¡Muy buena decisión preventiva! Si una aplicación sencilla exige permisos desproporcionados, "
                            "lo más sensato es desinstalarla y preferir las funciones nativas del sistema operativo."
                        ),
                    },
                ],
                "consejo_final": (
                    "Revisa periódicamente los permisos en los ajustes de tu teléfono. Si una app no necesita un dato "
                    "para su función declarada, no tiene por qué tener acceso a él."
                ),
            },
            ensure_ascii=False,
        ),
    },
]


def seed_actividades_iniciales() -> None:
    """Inserta actividades y simulaciones educativas para los temas correspondientes."""
    from app.models import Actividad, Tema

    temas = {tema.orden: tema for tema in db.session.scalars(select(Tema)).all()}

    for data in ACTIVIDADES_INICIALES:
        tema = temas.get(data["tema_orden"])
        if tema is None:
            continue

        actividad_existente = db.session.scalar(
            select(Actividad).where(
                Actividad.id_tema == tema.id_tema,
                Actividad.titulo == data["titulo"],
            )
        )
        if actividad_existente is None:
            nueva_actividad = Actividad(
                id_tema=tema.id_tema,
                titulo=data["titulo"],
                tipo=data["tipo"],
                instrucciones=data["instrucciones"],
                estado="publicado",
            )
            db.session.add(nueva_actividad)

    db.session.commit()


EVALUACIONES_INICIALES = [
    {
        "tema_orden": 1,
        "titulo": "Evaluación formativa: Contraseñas seguras y autenticación",
        "puntaje_minimo": 14.0,
        "preguntas": [
            {
                "enunciado": "¿Cuál es la característica técnica más determinante para la resistencia de una contraseña frente a ataques automatizados de fuerza bruta?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "La cantidad de símbolos especiales sustituyendo vocales simples.", "es_correcta": False},
                    {"texto": "La longitud total de la contraseña o frase de contraseña (passphrase).", "es_correcta": True},
                    {"texto": "Cambiar la contraseña cada semana utilizando secuencias numéricas consecutivas.", "es_correcta": False},
                    {"texto": "Utilizar el nombre de una mascota combinado con la fecha de nacimiento.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "¿Por qué la reutilización de una misma contraseña en múltiples plataformas representa un peligro grave de seguridad digital?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Porque las plataformas bloquean de forma automática a los usuarios con contraseñas similares.", "es_correcta": False},
                    {"texto": "Por el efecto dominó: si un servicio sufre una filtración, los atacantes probarán esa misma clave en el resto de tus cuentas.", "es_correcta": True},
                    {"texto": "Porque reduce la velocidad de conexión a internet del dispositivo.", "es_correcta": False},
                    {"texto": "Porque impide el envío de mensajes y correos electrónicos.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "¿Qué barrera defensiva proporciona la autenticación en dos pasos (2FA o MFA)?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Evita que recibas correo no deseado (spam) en tu bandeja de entrada.", "es_correcta": False},
                    {"texto": "Añade un cerrojo adicional requiriendo un código temporal en tu teléfono móvil además de tu contraseña para iniciar sesión.", "es_correcta": True},
                    {"texto": "Permite recuperar contraseñas olvidadas sin necesidad de verificar tu identidad.", "es_correcta": False},
                    {"texto": "Aumenta la memoria RAM de tu teléfono o computadora.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "Si un ciudadano de Guadalupe utiliza una computadora de uso público en una cabina o biblioteca, ¿cuál es la medida obligatoria antes de retirarse?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Dejar la ventana del navegador minimizada para el siguiente usuario.", "es_correcta": False},
                    {"texto": "Cerrar sesión de forma explícita en todas las cuentas y borrar el historial y datos de navegación de la sesión.", "es_correcta": True},
                    {"texto": "Apagar únicamente la pantalla del monitor.", "es_correcta": False},
                    {"texto": "Guardar la contraseña en el navegador para no olvidarla.", "es_correcta": False},
                ],
            },
        ],
    },
    {
        "tema_orden": 2,
        "titulo": "Evaluación formativa: Detección de phishing y fraudes digitales",
        "puntaje_minimo": 14.0,
        "preguntas": [
            {
                "enunciado": "¿Cuál es el objetivo principal de un ataque de phishing?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Comprobar la calidad de la conexión de fibra óptica en el distrito.", "es_correcta": False},
                    {"texto": "Engañar a la víctima suplantando una entidad legítima para robar credenciales, dinero o datos confidenciales.", "es_correcta": True},
                    {"texto": "Actualizar automáticamente las aplicaciones de un teléfono inteligente.", "es_correcta": False},
                    {"texto": "Proporcionar asistencia técnica municipal gratuita.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "Si recibes un correo supuestamente bancario que amenaza con el 'bloqueo inminente de tu cuenta en 2 horas', ¿cuál es el primer indicio de fraude?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Que el mensaje utilice un tono formal de saludo.", "es_correcta": False},
                    {"texto": "El sentido de extrema urgencia y amenaza de sanción para forzar una decisión impulsiva sin verificar.", "es_correcta": True},
                    {"texto": "Que la entidad financiera tenga oficinas físicas en el país.", "es_correcta": False},
                    {"texto": "Que el correo se haya enviado durante la mañana.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "Antes de hacer clic en un enlace recibido por mensaje o correo, ¿qué verificación técnica debes realizar siempre?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Verificar que el enlace aparezca subrayado en color azul.", "es_correcta": False},
                    {"texto": "Inspeccionar el dominio real de la URL, confirmando que coincida exactamente con el portal oficial (.gob.pe o .com.pe) y use HTTPS.", "es_correcta": True},
                    {"texto": "Reenviar el mensaje por grupos de redes sociales para pedir opiniones.", "es_correcta": False},
                    {"texto": "Hacer clic rápido y cerrar la ventana si parece sospechosa.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "¿Cuál es la recomendación correcta si sospechas que un mensaje o notificación es phishing?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Descargar y abrir los archivos adjuntos para verificar si son reales.", "es_correcta": False},
                    {"texto": "No pulsar el enlace, no responder con datos y verificar directamente por canales oficiales de atención al cliente.", "es_correcta": True},
                    {"texto": "Responder al correo solicitando que llamen a tu número personal.", "es_correcta": False},
                    {"texto": "Ingresar tu documento de identidad para consultar el estado.", "es_correcta": False},
                ],
            },
        ],
    },
    {
        "tema_orden": 3,
        "titulo": "Evaluación formativa: Privacidad y Protección de Datos (Ley 29733)",
        "puntaje_minimo": 14.0,
        "preguntas": [
            {
                "enunciado": "De acuerdo con la Ley N.° 29733 (Ley de Protección de Datos Personales del Perú), ¿qué exige el principio de consentimiento?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Que las empresas pueden vender bases de datos si los usuarios no reclaman en un año.", "es_correcta": False},
                    {"texto": "Que todo tratamiento de datos personales requiere la autorización previa, expresa, informada e inequívoca de su titular.", "es_correcta": True},
                    {"texto": "Que las contraseñas deben ser públicas para facilitar auditorías.", "es_correcta": False},
                    {"texto": "Que los datos personales se transfieran automáticamente a redes sociales.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "¿Qué establece el principio de proporcionalidad en el tratamiento de datos personales?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Que las aplicaciones deben solicitar todos los permisos posibles por si se ocupan después.", "es_correcta": False},
                    {"texto": "Que los datos solicitados deben ser únicamente los adecuados, pertinentes y no excesivos en relación con la finalidad determinada.", "es_correcta": True},
                    {"texto": "Que los usuarios deben pagar un costo proporcional al tamaño de su cuenta.", "es_correcta": False},
                    {"texto": "Que la contraseña debe ser proporcional al número de letras del nombre del usuario.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "¿Qué representan los derechos ARCO reconocidos por el marco normativo peruano?",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Archivar, Renombrar, Comprimir y Optimizar carpetas digitales.", "es_correcta": False},
                    {"texto": "Acceso, Rectificación, Cancelación y Oposición respecto al uso de tus datos personales.", "es_correcta": True},
                    {"texto": "Autenticación Rápida con Códigos de Operación bancaria.", "es_correcta": False},
                    {"texto": "Apertura de Redes y Conexiones Oficiales.", "es_correcta": False},
                ],
            },
            {
                "enunciado": "Si una aplicación de calculadora solicita permiso para acceder a tu libreta de contactos y ubicación GPS en tu teléfono móvil, debes:",
                "puntaje": 5.0,
                "alternativas": [
                    {"texto": "Aceptar todos los permisos sin dudar para que no se bloquee.", "es_correcta": False},
                    {"texto": "Denegar los permisos innecesarios o desinstalar la app por solicitar accesos desproporcionados a tu información privada.", "es_correcta": True},
                    {"texto": "Publicar tus contactos en línea para que nadie los robe.", "es_correcta": False},
                    {"texto": "Dejar la pantalla encendida permanentemente.", "es_correcta": False},
                ],
            },
        ],
    },
]


def seed_evaluaciones_iniciales() -> None:
    """Inserta evaluaciones, preguntas y alternativas pedagógicas para los temas correspondientes."""
    from app.models import Alternativa, Evaluacion, Pregunta, Tema

    temas = {tema.orden: tema for tema in db.session.scalars(select(Tema)).all()}

    for data_eval in EVALUACIONES_INICIALES:
        tema = temas.get(data_eval["tema_orden"])
        if tema is None:
            continue

        evaluacion = db.session.scalar(
            select(Evaluacion).where(
                Evaluacion.id_tema == tema.id_tema,
                Evaluacion.titulo == data_eval["titulo"],
            )
        )
        if evaluacion is None:
            evaluacion = Evaluacion(
                id_tema=tema.id_tema,
                titulo=data_eval["titulo"],
                puntaje_minimo=data_eval["puntaje_minimo"],
                estado="publicado",
            )
            db.session.add(evaluacion)
            db.session.flush()

        # Sembrar preguntas de la evaluación
        for data_preg in data_eval["preguntas"]:
            pregunta = db.session.scalar(
                select(Pregunta).where(
                    Pregunta.id_evaluacion == evaluacion.id_evaluacion,
                    Pregunta.enunciado == data_preg["enunciado"],
                )
            )
            if pregunta is None:
                pregunta = Pregunta(
                    id_evaluacion=evaluacion.id_evaluacion,
                    enunciado=data_preg["enunciado"],
                    puntaje=data_preg["puntaje"],
                )
                db.session.add(pregunta)
                db.session.flush()

                # Sembrar alternativas de la pregunta
                for data_alt in data_preg["alternativas"]:
                    alt = Alternativa(
                        id_pregunta=pregunta.id_pregunta,
                        texto=data_alt["texto"],
                        es_correcta=data_alt["es_correcta"],
                    )
                    db.session.add(alt)

    db.session.commit()
