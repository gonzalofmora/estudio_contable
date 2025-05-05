from estudio_contable.common.funciones_pub import afip_vep_aut_mon
from dotenv import dotenv_values

variables = dotenv_values()
user = variables.get('USER')
password = variables.get('PASSWORD')
tipo_vep = input('Monotributo (mon) o Autónomo (aut): ')
opcion_vep = int(input('Red Link (1) o PMC (2): '))
modo_manual = input('Automático (a) o manual (m): ').lower() == 'm'

afip_vep_aut_mon(user, password, tipo_vep, opcion_vep, modo_manual)