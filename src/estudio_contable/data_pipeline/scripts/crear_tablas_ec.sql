-- Tabla de comprobantes
CREATE TABLE IF NOT EXISTS comprobantes (
    "id_comprobante" INTEGER PRIMARY KEY,
    "tipo_comprobante" TEXT UNIQUE NOT NULL
          );

-- Tabla de clientes
DROP TABLE IF EXISTS clientes;
CREATE TABLE clientes (
    "id_cliente" INTEGER PRIMARY KEY AUTOINCREMENT,
    "nombre_cliente" TEXT UNIQUE NOT NULL,
    "cuit_cliente" TEXT UNIQUE NOT NULL,
    "cuit_afip" TEXT,
    "clave_afip" TEXT,
    "clave_arba" TEXT,
    "clave_agip" TEXT,
    "clave_seh" TEXT, 
    "usuario_seh" TEXT,
    "codigo_mis_comp" TEXT,
    "bajar_compras" INTEGER CHECK (bajar_compras IN (0, 1)),
    "bajar_compras_pi" INTEGER CHECK (bajar_compras_pi IN (0,1))
          );


-- Tabla de compras
CREATE TABLE IF NOT EXISTS compras (
    "id_compra" INTEGER PRIMARY KEY AUTOINCREMENT,
    "id_cliente" INTEGER,
    "fecha" DATE,
    "id_comprobante" INTEGER,
    "punto_de_venta" TEXT,
    "nro_de_comprobante" TEXT,
    "tipo_doc_emisor" TEXT,
    "nro_doc_emisor" TEXT,
    "emisor" TEXT,
    "importe_total" REAL,
    "moneda" TEXT,
    "tipo_de_cambio" REAL,
    "no_gravado" REAL,
    "exento" REAL,
    "crédito_fiscal_computable" REAL,
    "perc_o_pagos_otros_imp" REAL,
    "perc_iibb" REAL,
    "imp_municipales" REAL,
    "perc_o_pagos_iva" REAL,
    "imp_internos" REAL,
    "otros_tributos" REAL,
    "neto_0%" REAL,
    "neto_2,5%" REAL,
    "iva_2,5%" REAL,
    "neto_5%" REAL,
    "iva_5%" REAL,
    "neto_10,5%" REAL,
    "iva_10,5%" REAL,
    "neto_21%" REAL,
    "iva_21%" REAL,
    "neto_27%" REAL,
    "iva_27%" REAL,
    "total_neto_gravado" REAL,
    "total_iva" REAL,

    FOREIGN KEY ("id_comprobante") REFERENCES comprobantes("id_comprobantes")
    FOREIGN KEY ("id_cliente") REFERENCES clientes("id_cliente")
);

-- Tabla de ventas
CREATE TABLE IF NOT EXISTS ventas (
    "id_venta" INTEGER PRIMARY KEY AUTOINCREMENT,
    "id_cliente" INTEGER,
    "fecha" DATE,
    "id_comprobante" INTEGER,
    "punto_de_venta" TEXT,
    "nro_de_comprobante" TEXT,
    "tipo_doc_receptor" TEXT,
    "nro_doc_receptor" TEXT,
    "receptor" TEXT,
    "importe_total" REAL,
    "moneda" TEXT,
    "tipo_de_cambio" REAL,
    "no_gravado" REAL,
    "exento" REAL,
    "perc_o_pagos_otros_imp" REAL,
    "perc_iibb" REAL,
    "imp_municipales" REAL,
    "perc_no_categorizados" REAL,
    "imp_internos" REAL,
    "otros_tributos" REAL,
    "neto_0%" REAL,
    "neto_2,5%" REAL,
    "iva_2,5%" REAL,
    "neto_5%" REAL,
    "iva_5%" REAL,
    "neto_10,5%" REAL,
    "iva_10,5%" REAL,
    "neto_21%" REAL,
    "iva_21%" REAL,
    "neto_27%" REAL,
    "iva_27%" REAL,
    "total_neto_gravado" REAL,
    "total_iva" REAL,

    FOREIGN KEY ("id_comprobante") REFERENCES comprobantes("id_comprobantes")
    FOREIGN KEY ("id_cliente") REFERENCES clientes("id_cliente")
);
