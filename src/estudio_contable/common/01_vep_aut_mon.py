from estudio_contable.common.funciones_pub import afip_vep_aut_mon
from dotenv import dotenv_values

variables = dotenv_values()
user = variables.get('USER')
password = variables.get('PASSWORD')

afip_vep_aut_mon(user, password, 'aut')