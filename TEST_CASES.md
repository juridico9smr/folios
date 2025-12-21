# Casos de Prueba - Extractor de Propiedades

Este documento lista todos los casos de prueba que el extractor de propiedades debe manejar correctamente.

## Formatos de Separación

### 1. Formato con Dos Puntos (`:`)
```
3 -> 190172 : TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI
```
**Resultado esperado:** `TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI`

### 2. Formato con Guión (`-`)
```
3 -> 190172 - TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI
```
**Resultado esperado:** `TORRE 9 - APARTAMENTO 103 - PROYECTO MODIGLIANI`

### 3. Formato con Punto Simple (`.`)
```
3 -> 166319. CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709
```
**Resultado esperado:** `CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709`

### 4. Formato con Doble Punto (`..`)
```
3 -> 166457..CRA.33 #31-05-BLOQUE 2-SOTANO-CUARTO UTIL 9906
```
**Resultado esperado:** `CRA.33 #31-05-BLOQUE 2-SOTANO-CUARTO UTIL 9906`

### 5. Formato con Guión y Dos Puntos (`: -`)
```
42 -> 1083489 : - APARTAMENTO 503 TORRE 3
```
**Resultado esperado:** `APARTAMENTO 503 TORRE 3`

### 6. Formato Concatenado (sin separador)
```
4 -> 230510APTO 0129 - TORRE 8 - ETAPA I
```
**Resultado esperado:** `APTO 0129 - TORRE 8 - ETAPA I`

## Propiedades Multilínea

### 7. Propiedad en Múltiples Líneas Consecutivas
```
2 -> 261841 : APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO
DOS -
```
**Resultado esperado:** `APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO DOS`

### 8. Propiedad Dividida Entre Páginas (con headers/footers)
```
2 -> 262148 : APARTAMENTO NUMERO SEISCIENTOS SIETE (607) ETAPA II TORRE 1: UBICADO EN EL
La validez de este documento podrá verificarse en la página certificados.supernotariado.gov.co
OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MANIZALES
CERTIFICADO DE TRADICION
MATRICULA INMOBILIARIA
EL SEXTO PISO -
```
**Resultado esperado:** `APARTAMENTO NUMERO SEISCIENTOS SIETE (607) ETAPA II TORRE 1: UBICADO EN EL SEXTO PISO`

### 9. Propiedad con Dos Puntos Dentro del Nombre
```
2 -> 262089 : APARTAMENTO NUMERO CIENTO DOS (102) ETAPA II TORRE 1: UBICADO EN EL
PRIMER PISO -
```
**Resultado esperado:** `APARTAMENTO NUMERO CIENTO DOS (102) ETAPA II TORRE 1: UBICADO EN EL PRIMER PISO`

## Casos Especiales

### 10. Propiedad que Termina con "ETAPA -"
```
3 -> 214074 : APARTAMENTO 108 TORRE 6 CONJUNTO CERRADO PORTOBELO II ETAPA -
```
**Resultado esperado:** `APARTAMENTO 108 TORRE 6 CONJUNTO CERRADO PORTOBELO II ETAPA -`
**Nota:** El guión al final debe mantenerse si es parte del nombre de la propiedad.

### 11. Propiedad con Números y Símbolos
```
3 -> 166319. CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709
```
**Resultado esperado:** `CRA.33 #31-35-BLOQUE 2-PISO 7 APTO.709`

### 12. Propiedad con Palabras en Números (Escritas)
```
2 -> 262132 : APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL
QUINTO PISO -
```
**Resultado esperado:** `APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL QUINTO PISO`

## Tipos de Inmuebles

### 13. Apartamento
```
8 -> 251666 : CONJUNTO RESIDENCIAL VENTURA - PROPIEDAD HORIZONTAL TORRE 1 APARTAMENTO 101
```
**Resultado esperado:** `CONJUNTO RESIDENCIAL VENTURA - PROPIEDAD HORIZONTAL TORRE 1 APARTAMENTO 101`

### 14. Parqueadero
```
6 -> 312770 : PARQUEADERO MOTOS 2 CON DEPOSITO
```
**Resultado esperado:** `PARQUEADERO MOTOS 2 CON DEPOSITO`
**Nota:** NO debe agregar "APARTAMENTO" si no está en el certificado.

### 15. Local
```
6 -> 789012LOCAL 5 - PISO 1
```
**Resultado esperado:** `LOCAL 5 - PISO 1`

### 16. Depósito
```
7 -> 345678DEPOSITO 10
```
**Resultado esperado:** `DEPOSITO 10`

### 17. Bodega
```
10 -> 111222BODEGA 5
```
**Resultado esperado:** `BODEGA 5`

## Formatos de Círculo

### 18. Círculo Tradicional (solo números)
```
176-0998349
```
**Resultado esperado:** Círculo: `176`, Folio: `0998349`

### 19. Círculo con Letra
```
51N-0998349
```
**Resultado esperado:** Círculo: `51N`, Folio: `0998349`

## Filtrado de Headers/Footers

### 20. Headers/Footers Deben Ser Filtrados
```
2 -> 262173 : APARTAMENTO NUMERO OCHOCIENTOS DIEZ (810) ETAPA II TORRE 1: UBICADO EN
EL OCTAVO PISO -
La validez de este documento podrá verificarse en la página certificados.supernotariado.gov.co
OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MANIZALES
CERTIFICADO DE TRADICION
MATRICULA INMOBILIARIA
```
**Resultado esperado:** `APARTAMENTO NUMERO OCHOCIENTOS DIEZ (810) ETAPA II TORRE 1: UBICADO EN EL OCTAVO PISO`
**Nota:** No debe incluir los headers/footers en el resultado.

### 21. Salvedades Deben Ser Filtradas
```
2 -> 262173 : APARTAMENTO NUMERO CUATROCIENTOS TRES (403) ETAPA II TORRE 1: UBICADO EN EL CUARTO PISO - OFICINA DE REGISTRO DE INSTRUMENTOS PUBLICOS DE MANIZALES CERTIFICADO DE TRADICION MATRICULA INMOBILIARIALa validez de este documento podrá verificarse en la página certificados.supernotariado.gov.co Certificado generado con el Pin No: 2511195352124777447Nro Matrícula: 100-256825,100-262122,,,
```
**Resultado esperado:** `APARTAMENTO NUMERO CUATROCIENTOS TRES (403) ETAPA II TORRE 1: UBICADO EN EL CUARTO PISO`
**Nota:** Debe remover toda la información de headers/footers concatenada.

## Casos de Incompletitud

### 22. Propiedad Incompleta que Termina con "EN EL"
```
2 -> 262132 : APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL
QUINTO PISO -
```
**Resultado esperado:** `APARTAMENTO NUMERO QUINIENTOS DOS (502) ETAPA II TORRE 1: UBICADO EN EL QUINTO PISO`

### 23. Propiedad Incompleta que Termina con "PISO"
```
2 -> 261841 : APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO
DOS -
```
**Resultado esperado:** `APARTAMENTO NUMERO DOSCIENTOS UNO (201) TORRE 4: UBICADO EN EL PISO DOS`

## Notas Importantes

1. **Exactitud**: El nombre de la propiedad debe copiarse exactamente como aparece en el certificado, sin agregar información que no esté presente.

2. **Limpieza**: Se deben remover:
   - Headers y footers del PDF
   - Números de matrícula residuales
   - Guiones y puntos al final SOLO si no son parte del nombre (ej: "ETAPA -" debe mantenerse)

3. **Multilínea**: El script debe manejar propiedades que están divididas en múltiples líneas, incluso entre páginas.

4. **Robustez**: Debe funcionar con diferentes formatos de separación y tipos de inmuebles.

5. **Círculos**: Debe aceptar círculos con formato numérico (`176`) o alfanumérico (`51N`).

