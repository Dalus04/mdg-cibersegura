-- ==============================================================================
-- MDG CIBERSEGURA - SCRIPT DE CREACIÓN DE BASE DE DATOS (MYSQL / MARIADB)
-- Municipalidad Distrital de Guadalupe - Subgerencia de Informática y TI
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS mdg_cibersegura
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE mdg_cibersegura;

-- ------------------------------------------------------------------------------
-- 1. TABLA: rol
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. TABLA: usuario
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    id_rol INT NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    correo VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(512) NOT NULL,
    estado VARCHAR(20) NOT NULL DEFAULT 'activo',
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES rol (id_rol)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. TABLA: tema
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tema (
    id_tema INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    descripcion TEXT,
    orden INT NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'publicado'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. TABLA: contenido (Lecciones educativas)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contenido (
    id_contenido INT AUTO_INCREMENT PRIMARY KEY,
    id_tema INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    contenido TEXT NOT NULL,
    orden INT NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'publicado',
    CONSTRAINT fk_contenido_tema FOREIGN KEY (id_tema) REFERENCES tema (id_tema)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. TABLA: actividad
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actividad (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    id_tema INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    instrucciones TEXT,
    estado VARCHAR(20) NOT NULL DEFAULT 'publicado',
    CONSTRAINT fk_actividad_tema FOREIGN KEY (id_tema) REFERENCES tema (id_tema)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 6. TABLA: evaluacion
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS evaluacion (
    id_evaluacion INT AUTO_INCREMENT PRIMARY KEY,
    id_tema INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    puntaje_minimo FLOAT NOT NULL DEFAULT 0,
    estado VARCHAR(20) NOT NULL DEFAULT 'publicado',
    CONSTRAINT fk_evaluacion_tema FOREIGN KEY (id_tema) REFERENCES tema (id_tema)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 7. TABLA: pregunta
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pregunta (
    id_pregunta INT AUTO_INCREMENT PRIMARY KEY,
    id_evaluacion INT NOT NULL,
    enunciado TEXT NOT NULL,
    puntaje FLOAT NOT NULL DEFAULT 1,
    CONSTRAINT fk_pregunta_evaluacion FOREIGN KEY (id_evaluacion) REFERENCES evaluacion (id_evaluacion)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 8. TABLA: alternativa
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alternativa (
    id_alternativa INT AUTO_INCREMENT PRIMARY KEY,
    id_pregunta INT NOT NULL,
    texto TEXT NOT NULL,
    es_correcta BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_alternativa_pregunta FOREIGN KEY (id_pregunta) REFERENCES pregunta (id_pregunta)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 9. TABLA: progreso_contenido
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS progreso_contenido (
    id_progreso INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_contenido INT NOT NULL,
    completado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_completado DATETIME NULL,
    CONSTRAINT uq_progreso_usuario_contenido UNIQUE (id_usuario, id_contenido),
    CONSTRAINT fk_progreso_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_progreso_contenido FOREIGN KEY (id_contenido) REFERENCES contenido (id_contenido)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 10. TABLA: intento_actividad
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS intento_actividad (
    id_intento_actividad INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_actividad INT NOT NULL,
    resultado VARCHAR(100),
    fecha_intento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_intento_act_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_intento_act_actividad FOREIGN KEY (id_actividad) REFERENCES actividad (id_actividad)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 11. TABLA: intento_evaluacion
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS intento_evaluacion (
    id_intento_evaluacion INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NOT NULL,
    id_evaluacion INT NOT NULL,
    puntaje_obtenido FLOAT NOT NULL DEFAULT 0,
    fecha_intento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_intento_eva_usuario FOREIGN KEY (id_usuario) REFERENCES usuario (id_usuario)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_intento_eva_evaluacion FOREIGN KEY (id_evaluacion) REFERENCES evaluacion (id_evaluacion)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 12. TABLA: respuesta
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS respuesta (
    id_respuesta INT AUTO_INCREMENT PRIMARY KEY,
    id_intento_evaluacion INT NOT NULL,
    id_pregunta INT NOT NULL,
    id_alternativa INT NOT NULL,
    CONSTRAINT fk_respuesta_intento FOREIGN KEY (id_intento_evaluacion) REFERENCES intento_evaluacion (id_intento_evaluacion)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_respuesta_pregunta FOREIGN KEY (id_pregunta) REFERENCES pregunta (id_pregunta)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_respuesta_alternativa FOREIGN KEY (id_alternativa) REFERENCES alternativa (id_alternativa)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- DATOS INICIALES (SEMILLAS)
-- ==============================================================================

-- Roles iniciales
INSERT INTO rol (id_rol, nombre, descripcion) VALUES
(1, 'ciudadano', 'Usuario público de la plataforma educativa.'),
(2, 'administrador', 'Gestiona contenidos, actividades y evaluaciones.')
ON DUPLICATE KEY UPDATE descripcion=VALUES(descripcion);

-- Temas iniciales
INSERT INTO tema (id_tema, titulo, descripcion, orden, estado) VALUES
(1, 'Gestión de contraseñas seguras y autenticación', 'Aprende a crear claves robustas, evitar patrones predecibles y utilizar la autenticación en dos pasos para proteger tus cuentas personales e institucionales.', 1, 'publicado'),
(2, 'Detección de enlaces fraudulentos y phishing', 'Identifica correos engañosos, mensajes de texto fraudulentos (smishing) y sitios web falsos que buscan suplantar identidades para robar credenciales y dinero.', 2, 'publicado'),
(3, 'Protección de datos personales y privacidad digital', 'Conoce la importancia de proteger tus datos personales conforme al marco normativo y aprende a minimizar tu huella digital frente a terceros.', 3, 'publicado'),
(4, 'Navegación segura y redes Wi-Fi públicas', 'Prácticas seguras para navegar en internet desde el hogar, el trabajo o redes inalámbricas abiertas.', 4, 'publicado')
ON DUPLICATE KEY UPDATE titulo=VALUES(titulo);

-- ------------------------------------------------------------------------------
-- Usuarios iniciales para pruebas (claves hasheadas con Werkzeug / scrypt)
-- Contraseña para admin@guadalupe.gob.pe: Admin1234!
-- Contraseña para ciudadano@ejemplo.com:  Ciudadano123!
-- ------------------------------------------------------------------------------
INSERT INTO usuario (id_usuario, id_rol, nombres, apellidos, correo, password_hash, estado, fecha_registro) VALUES
(1, 2, 'Administrador', 'Municipal', 'admin@guadalupe.gob.pe', 'scrypt:32768:8:1$nJtkXnCP65NHrAkA$52ca4e3fc585f1caf52355a4e15253c9f9121a60439c60d19458d6a4b1d6e71132bf5682bc6d18e8297e2a71f25057bcdc26b096a0333b70caa6dbd0020ddb5f', 'activo', NOW()),
(2, 1, 'Ciudadano', 'Ejemplo', 'ciudadano@ejemplo.com', 'scrypt:32768:8:1$dSq3RHzEwso9rXmT$1ad31aa0dc97953d40ee02a62758f1aac662c157cfb05f1931509c89d65b3cc2fe320ec96cfb9d897d81308c79dd8d469c3001d106db951a24090a29ecf6d0e8', 'activo', NOW())
ON DUPLICATE KEY UPDATE correo=VALUES(correo);

