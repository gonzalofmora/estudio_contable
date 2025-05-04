from estudio_contable.common.funciones_pub import extraer_todos_los_comprobantes, mc_pre_procesamiento_ventas_csv, mc_insertar_ventas_raw
from pathlib import Path
from dotenv import dotenv_values

variables = dotenv_values()

#db_path = Path.cwd().parent / 'estudio_contable_pub.db'

carpeta_ventas                    = Path(variables.get('MC_ZIPS'))
carpeta_destino_csv_raw           = Path(variables.get('MC_CARPETA_VENTAS_RAW_CSV'))
carpeta_destino_csv_raw.mkdir(parents=True, exist_ok=True)
carpeta_destino_csv_pre_processed = Path(variables.get('MC_CARPETA_VENTAS_PP_CSV'))
carpeta_destino_csv_pre_processed.mkdir(parents=True, exist_ok=True)

extraer_todos_los_comprobantes(carpeta_ventas)

archivos_csv = list(carpeta_ventas.glob('*.csv'))

for archivo in archivos_csv:
    destino_archivo_raw = carpeta_destino_csv_raw / f'{archivo.stem}.csv'
    nombre_csv_pre_processed = f'mc_ventas_{archivo.stem.split()[0][45:]}.csv'
    destino_csv_pre_processed = carpeta_destino_csv_pre_processed / nombre_csv_pre_processed

    df = mc_pre_procesamiento_ventas_csv(archivo)
    cantidad_insertada = mc_insertar_ventas_raw(df)
    print(f'Se insertaron {cantidad_insertada} comprobantes en la base de datos')

    archivo.replace(destino_archivo_raw)
    df.to_csv(destino_csv_pre_processed, index=False)



# Problema: ¿cómo evitar que python tenga que intentar agregar todos los comprobantes de la carpeta de comprobantes?

# Tendría que extraerlos a la misma carpeta de los zips, cargarlos desde ahí y posteriormente enviarlos a su carpeta de destino final. 