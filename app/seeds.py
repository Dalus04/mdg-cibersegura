from sqlalchemy import select

from app.extensions import db
from app.models import Contenido, Tema

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
