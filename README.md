# Proyecto de Fin de Grado

Este proyecto es parte de mi trabajo de fin de grado en la Universidad Francisco de Vitoria. Utiliza Terraform CDKTF para gestionar la infraestructura como código.

## Descripción del Proyecto

El proyecto utiliza Terraform CDKTF para definir la infraestructura de forma programática. Una de las características importantes es la gestión de credenciales, donde se incorpora un archivo que contiene todas las variables de credenciales necesarias para la ejecución del proyecto.

## Archivo de Credenciales

En este proyecto, se proporciona una plantilla para el archivo de credenciales llamada `credentials.py.example`. Este archivo debe ser completado con las credenciales adecuadas antes de ejecutar el código.

## Terraform CDKTF

Terraform CDKTF es una herramienta que permite definir la infraestructura como código utilizando lenguajes de programación como Python. Esto proporciona una manera más programática y flexible de definir y gestionar la infraestructura en la nube.

## Ejecución del Proyecto

Antes de ejecutar el proyecto, asegúrate de completar el archivo de credenciales `credentials.py.example` con la información correcta y renombrarlo a `credentials.py`.

Una vez que las credenciales estén configuradas, puedes ejecutar el proyecto utilizando los comandos estándar de Terraform CDKTF.

```bash
# Instalar dependencias
npm install

# Compilar y desplegar la infraestructura
cdktf deploy

# Destruir la infraestructura
cdktf destroy
