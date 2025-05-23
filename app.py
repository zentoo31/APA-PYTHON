from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json
from ia_sistema import predecir_clase_gbot, obtener_respuesta_gbot, intenciones_gbot
from etl import etl_process 
from dotenv import load_dotenv
import os

# Configuración inicial
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Reduce logs de TensorFlow
load_dotenv()

app = Flask(__name__)

# Configuración CORS
cors = CORS(app, resources={
    r"/chatbot": {"origins": os.getenv('ORIGIN')},
    r"/run_etl_process": {"origins": os.getenv('ORIGIN')}
})

# Endpoint del chatbot
@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        content = request.get_json()
        user_input = content['message']
        
        intents_list = predecir_clase_gbot(user_input)
        response = obtener_respuesta_gbot(intents_list, intenciones_gbot)
    
        return jsonify({"response": response})
    
    except KeyError:
        return jsonify({"error": "Campo 'message' no encontrado en la solicitud"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Endpoint ETL
@app.route('/run_etl_process', methods=['GET'])
def run_etl_process():
    try:
        result = etl_process()
        return jsonify({'message': 'Proceso ETL ejecutado exitosamente', 'result': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Configuración para producción
if __name__ == '__main__':
    app.run(
        host='0.0.0.0',  # Acepta conexiones externas
        port=int(os.environ.get('PORT', 5000)),  # Usa el puerto de Render o 5000 por defecto
        debug=False  # ¡Importante! Desactiva debug en producción
    )