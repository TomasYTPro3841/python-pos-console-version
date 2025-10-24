# python-pos
Es un programa POS hecho en python, tiene UI por consola o grafico con Tkinter desde la version 1.3.0
Simplemente instala python y ejecuta el servidor con:
python server_pos.py
Es un programa y funciona con sqlite, si pide una dependencia solo instálala, las dependencias se incluyen en un txt dentro del .zip de la release desde la versión 1.3.0 los recibos son en .txt
Se hizo con chatgpt.
Se pueden programar teclas para realizar acciones especificas desde la versión 1.2.0, aquí la lista de acciones:
Menú principal
| Acción interna   | Descripción                       |
| ---------------- | --------------------------------- |
| `list_products`  | Listar todos los productos        |
| `add_product`    | Añadir un nuevo producto          |
| `update_product` | Actualizar un producto existente  |
| `delete_product` | Eliminar un producto              |
| `start_sale`     | Iniciar una venta (abrir carrito) |
| `report_sales`   | Ver reporte de ventas por fecha   |
| `export_csv`     | Exportar ventas a CSV             |
| `exit`           | Salir del programa                |

Dentro del carrito / venta
| Acción interna           | Descripción                           |
| ------------------------ | ------------------------------------- |
| `add_item`               | Añadir artículo por código al carrito |
| `remove_item`            | Quitar artículo del carrito           |
| `change_qty`             | Cambiar cantidad de un artículo       |
| `view_cart`              | Ver contenido del carrito             |
| `apply_discount_percent` | Aplicar descuento en porcentaje       |
| `apply_discount_amount`  | Aplicar descuento en cantidad fija    |
| `process_sale`           | Procesar venta y pagar                |
| `cancel_sale`            | Cancelar la venta actual              |

Siempre uno por línea. Se escriben en binded_keys.txt de esta forma:
accion=tecla
Ejemplo: add_item=a o process_sale=enter
