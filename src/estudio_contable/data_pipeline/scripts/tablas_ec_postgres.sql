CREATE TABLE IF NOT EXISTS ventas_raw (
    id_venta_raw             INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha                    DATE,
    tipo_de_comprobante      TEXT,
    punto_de_venta           TEXT,
    nro_de_comprobante_desde TEXT,
    nro_de_comprobante_hasta TEXT,
    cod_autorizacion         TEXT,
    tipo_doc_receptor        TEXT,
    nro_doc_receptor         TEXT,
    receptor                 TEXT,
    tipo_de_cambio           NUMERIC(10,2),
    moneda                   TEXT,
    neto_gravado             NUMERIC(10,2),
    no_gravado               NUMERIC(10,2),
    exento                   NUMERIC(10,2),
    otros_tributos           NUMERIC(10,2),
    iva                      NUMERIC(10,2),
    importe_total            NUMERIC(10,2),
    porcentaje_iva           NUMERIC(10,2),
    cuit_cliente             TEXT,
    fecha_descarga           DATE,
    UNIQUE(punto_de_venta, nro_de_comprobante_desde, nro_doc_receptor)
);

DROP TABLE IF EXISTS clientes;
CREATE TABLE clientes (
    id_cliente      INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    cliente         TEXT UNIQUE,
    razon_social    TEXT UNIQUE,
    cuit_cliente    TEXT UNIQUE,
    cuit_afip       TEXT,
    clave_afip      TEXT,
    clave_arba      TEXT,
    clave_agip      TEXT,
    usuario_seh     TEXT,
    clave_seh       TEXT,
    codigo_mis_comp INTEGER
);

