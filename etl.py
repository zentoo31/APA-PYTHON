from flask import Flask, jsonify
from flask_cors import CORS
import pymssql
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

def extract_data(conn, query):
    return pd.read_sql(query, conn)

def transform_data(df):
    # Aquí puedes aplicar cualquier transformación necesaria
    return df

def delete_existing_data(conn, table_name, primary_keys, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        where_clause = " AND ".join([f"{pk} = %s" for pk in primary_keys])
        cursor.execute(f"DELETE FROM [dbo].[{table_name}] WHERE {where_clause}", [row[pk] for pk in primary_keys])
    conn.commit()

def load_tiempo(conn, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_TIEMPO_DEST] (
            fechaInicio, DiaInicio, MesInicio, DiaFinal, MesFinal, 
            Turno, DiaDeClases, Semestre, Año
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, 
        (row['fechaInicio'], row['DiaInicio'], row['MesInicio'], row['DiaFinal'],
         row['MesFinal'], row['Turno'], row['DiaDeClases'], row['Semestre'], row['Año']))
    conn.commit()
    
def load_estudiantes(conn, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_ESTUDIANTES_DEST] (
            CodigoE, dniE, nombresE, apellidosE, descripcion, 
            correo, descripcionE, celular, direccion, 
            descripcionD, descripcionCon
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, 
        (row['CodigoE'], row['dniE'], row['nombresE'], row['apellidosE'],
         row['descripcion'], row['correo'], row['descripcionE'], row['celular'],
         row['direccion'], row['descripcionD'], row['descripcionCon']))
    conn.commit()

def load_categorias(conn, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_CATEGORIA_DEST](idCategoriaE, Categoria) VALUES (%s,%s)
        """,
        (row['idCategoriaE'], row['descripcionCE']))
    conn.commit()
    
def load_carreras(conn, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_CARRERA_DEST] (
            idCarrera, nombreCarrera, descripcionFa
        ) VALUES (%s, %s, %s)
        """, 
        (row['idCarrera'], row['nombreCarrera'], row['descripcionFa']))
    conn.commit()
    
def load_unidades(conn, df):
    cursor= conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_UNIDAD_DEST](
            idUnidad, descripcionU
        ) VALUES (%s,%s)
        """,
        (row['idUnidad'], row['descripcionU']))
    conn.commit()    
    
def load_tipos(conn, df):
    cursor= conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_TIPOCALIFICACION_DEST](
            idTipo, descripcion
        ) VALUES (%s,%s)
        """,
        (row['idTipo'], row['descripcion']))
    conn.commit()   
    
def load_cursos(conn, df):
    cursor= conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_CURSO_DEST](
            idCurso, NombreCurso, NumeroCreditos, CategoriaCurso, Ciclo
        ) VALUES (%s, %s, %s, %s, %s)
        """,
        (row['idCurso'], row['NombreCurso'], row['NumeroCreditos'], row['descripcionCC'], row['ciclo']))
    conn.commit()             

def load_profesores(conn, df):
    cursor= conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_PROFESOR_DEST](
            codigoD, dniProf, nombresD, apellidosD, genero, estadoCivil, correo, celular, direccion, distrito
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)            
        """,
        (row['codigoD'], row['dniProf'], row['nombresD'], row['apellidosD'], row['descripcion'], row['descripcionE'], row['correo'], row['celular'], row['direccion'], row['descripcionD']))
    conn.commit()

def load_ambiente(conn, df):
    cursor= conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[DIM_AMBIENTE_DEST](
            aula, idPabellon
        ) VALUES (%s,%s)              
        """,
        (row['aula'], row['idPabellon']))
    conn.commit()
    
def load_desempeno(conn, df):
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute("""
        INSERT INTO [dbo].[H_DESEMPEÑO_DEST] (
            nota, idUnidad, idTipo, codigoE, idCategoriaE, 
            idCurso, idCarrera, codigoD, fechaInicio, Turno, aula, Pabellon
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, 
        (row['nota'], row['idUnidad'], row['idTipo'], row['codigoE'], row['idCategoriaE'], 
         row['idCurso'], row['idCarrera'], row['codigoD'], row['fechaInicio'], row['Turno'], 
         row['aula'], row['Pabellon']))
    conn.commit()
    
def etl_process():
    try:
        conn_dimensional = pymssql.connect(
            server=os.getenv('SQL_SERVER'),         # Por ejemplo: 'mi-servidor.database.windows.net'
            user=os.getenv('SQL_USER'),             # Usuario de Azure SQL
            password=os.getenv('SQL_PASSWORD'),     # Contraseña
            database=os.getenv('SQL_DB_DIMENSIONAL'),
            port=1433,
            encrypt=True,
            trust_server_certificate=False,         # Para verificar el certificado SSL
            login_timeout=30
        )

        conn_relacional = pymssql.connect(
            server=os.getenv('SQL_SERVER'),
            user=os.getenv('SQL_USER'),
            password=os.getenv('SQL_PASSWORD'),
            database=os.getenv('SQL_DB_RELACIONAL'),
            port=1433,
            encrypt=True,
            trust_server_certificate=False,
            login_timeout=30
        )
        
        queries = [
            {
                "query": """
                    SELECT DISTINCT (fechaInicio),
                        DAY(fechaInicio) AS DiaInicio,
                        MONTH(fechaInicio) AS MesInicio,
                        DAY(fechaTermino) AS DiaFinal,
                        MONTH(fechaTermino) AS MesFinal,
                        idTurno as Turno,
                        CASE 
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 1 THEN 'Domingo'
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 2 THEN 'Lunes'
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 3 THEN 'Martes'
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 4 THEN 'Miércoles'
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 5 THEN 'Jueves'
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 6 THEN 'Viernes'
                            WHEN DATEPART(WEEKDAY, fechaInicio) = 7 THEN 'Sábado'
                        END AS DiaDeClases,
                        CASE 
                            WHEN MONTH(fechaInicio) BETWEEN 1 AND 6 THEN 'Primer Semestre'
                            ELSE 'Segundo Semestre'
                        END AS Semestre,
                        YEAR(fechaInicio) AS Año 
                    FROM  DetalleMatricula De;
                """,
                "load_function": load_tiempo,
                "table_name": "DIM_TIEMPO_DEST",
                "primary_key_column": ["fechaInicio", "Turno"]
            },
            
            {
                "query": """
                    SELECT E.CodigoE, E.dniE, E.nombresE, E.apellidosE, G.descripcion AS descripcion, 
                           E.correo, C.descripcionE, E.celular, E.direccion, 
                           D.descripcionD, Cs.descripcionCon
                    FROM Estudiante E 
                    INNER JOIN Genero G ON G.idGenero = E.idGenero
                    INNER JOIN EstadoCivil C ON C.idEstado = E.idEstado
                    INNER JOIN Distrito D ON D.idDistrito = E.idDistrito
                    INNER JOIN CondicionSocioEconomica Cs ON Cs.idCondicionSE = E.idCondicionSE;
                """,
                "load_function": load_estudiantes,
                "table_name": "DIM_ESTUDIANTES_DEST",
                "primary_key_column": ["CodigoE"]
            },
            {
                "query": """
                    SELECT idCategoriaE, descripcionCE FROM CategoriaEstudiante;
                """,
                "load_function": load_categorias,
                "table_name": "DIM_CATEGORIA_DEST",
                "primary_key_column": ["idCategoriaE"]
            },
            {
                               "query": """
                  SELECT c.idCarrera, c.nombreCarrera, F.descripcionFa FROM Carrera c inner join Facultad F on F.idFacultad= c.idFacultad;
                """,
                "load_function": load_carreras,
                "table_name": "DIM_CARRERA_DEST",
                "primary_key_column": ["idCarrera"]
            },
            {
                "query": """
                    SELECT idUnidad, descripcionU FROM Unidad;
                """,
                "load_function": load_unidades,
                "table_name": "DIM_UNIDAD_DEST",
                "primary_key_column": ["idUnidad"]
            },
            {
                "query": """
                    SELECT idTipo, descripcion FROM Tipo;
                """,
                "load_function": load_tipos,
                "table_name": "DIM_TIPOCALIFICACION_DEST",
                "primary_key_column": ["idTipo"]
            },
            {
                "query": """
                      SELECT c.idCurso, c.NombreCurso, c.NumeroCreditos, Ca.descripcionCC, cl.decripcion as ciclo 
                    FROM Curso c INNER JOIN CategoriaCurso Ca ON Ca.idCategoriaCurso = c.idCategoriaCurso
					inner join Ciclo cl on cl.idCiclo= c.idCiclo;
                """,
                "load_function": load_cursos,
                "table_name": "DIM_CURSO_DEST",
                "primary_key_column": ["idCurso"]
            },
            {
                "query": """
                    SELECT P.codigoD, P.dniProf, P.nombresD, P.apellidosD, G.descripcion, 
                           EC.descripcionE, P.correo, P.celular, P.direccion, 
                           D.descripcionD 
                    FROM Profesor P 
                    INNER JOIN Genero G ON G.idGenero = P.idGenero
                    INNER JOIN EstadoCivil EC ON EC.idEstado = P.idEstado
                    INNER JOIN Distrito D ON D.idDistrito = P.idDistrito;
                """,
                "load_function": load_profesores,
                "table_name": "DIM_PROFESOR_DEST",
                "primary_key_column": ["codigoD"]
            },
            {
                "query": """
                         SELECT Distinct aula, idPabellon FROM DetalleMatricula  order by  aula
                """,
                "load_function": load_ambiente,
                "table_name": "DIM_AMBIENTE_DEST",
                "primary_key_column": ["aula", "idPabellon"]
            },
            {
                "query": """
                    SELECT 
                    Dn.nota, 
                    U.idUnidad, 
                    T.idTipo, 
                    E.codigoE, 
                    Ce.idCategoriaE, 
                    C.idCurso, 
                    E.idCarrera, 
                    P.codigoD, 
                    Dm.fechaInicio, 
                    Dm.idTurno AS Turno, 
                    Dm.aula, 
                    Dm.idPabellon AS Pabellon
                FROM DetalleNota Dn
                INNER JOIN Tipo T ON T.idTipo = Dn.idTipo
                INNER JOIN Unidad U ON U.idUnidad = Dn.idUnidad
                INNER JOIN Notas N ON N.idNota = Dn.idNota
                INNER JOIN DetalleMatricula Dm ON Dm.idDetalleMatricula = N.idDetalleMatricula
                INNER JOIN Curso C ON C.idCurso = Dm.idCurso
                INNER JOIN Profesor P ON P.codigoD = Dm.codigoD
                INNER JOIN Matricula M ON M.idMatricula = Dm.idMatricula
                INNER JOIN Estudiante E ON E.codigoE = M.codigoE
                INNER JOIN CategoriaEstudiante Ce ON Ce.idCategoriaE = E.idCategoriaE;
                """,
                "load_function": load_desempeno,
                "table_name": "H_DESEMPEÑO_DEST",
                "primary_key_column": ["nota", "idUnidad", "idTipo", "codigoE", "idCategoriaE", "idCurso", "idCarrera", "codigoD", "fechaInicio", "Turno", "aula", "Pabellon"]
            },
            
        ]
        
        cursor = conn_dimensional.cursor()
        cursor.execute("DELETE FROM [dbo].[H_DESEMPEÑO_DEST]")
        conn_dimensional.commit()

        for item in queries:
            df = extract_data(conn_relacional, item["query"])
            df_transformed = transform_data(df)
            
            # Eliminar registros existentes antes de la carga
            delete_existing_data(conn_dimensional, item["table_name"], item["primary_key_column"], df_transformed)
            
            # Cargar los datos transformados
            item["load_function"](conn_dimensional, df_transformed)

        conn_relacional.close()
        conn_dimensional.close()

        return "Proceso ETL ejecutado exitosamente"

    except pymssql.Error as e:
        return f"Error de base de datos: {str(e)}"
    
    except Exception as e:
        return f"Error desconocido: {str(e)}"

etl_process()
