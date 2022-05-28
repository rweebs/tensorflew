from inferenceutils import *
import psycopg2
import imghdr
import io
from flask import Flask, render_template, request, redirect, url_for, abort, \
    send_from_directory, jsonify, make_response
from werkzeug.utils import secure_filename
import os

labelmap_path = 'labelmap.pbtxt'

category_index = label_map_util.create_category_index_from_labelmap(labelmap_path, use_display_name=True)
tf.keras.backend.clear_session()
model = tf.saved_model.load(f'saved_model')

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.png', '.gif']
app.config['UPLOAD_PATH'] = './uploads'

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return None
    return '.' + (format if format != 'jpeg' else 'jpg')

@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413

@app.route('/')
def index():
    files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('index.html', files=files)

@app.route('/', methods=['POST'])
def upload_files():
    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    buffer = io.BytesIO()
    uploaded_file.save(buffer)

    image_np = load_image_into_array(uploaded_file)
    output_dict = run_inference_for_single_image(model, image_np)
    threshold = 0.5
    food_predict = []
    for i in range(len(output_dict['detection_scores'])):
        if output_dict['detection_scores'][i] > threshold:
            label = output_dict['detection_classes'][i]
            name = category_index[label]
            if name not in food_predict:
                food_predict.append(name.get('name'))
    print(filename)
    print("output dict:",output_dict)
    conn = psycopg2.connect(
    host="35.240.162.20",
    database="serantau",
    user="postgres",
    password="SqGKguYA5XZ6_1rT")

    t = tuple(food_predict)
    cur = conn.cursor()
    result = []
    if len(food_predict)>0:
        cur.execute(f"select * from models where name in {t}")
        rows = cur.fetchall()
    
        for row in rows:
            temp = {
                    'name': row[1],
                    'category': row[2],
                    'calorie': row[3],
                    'fat': row[4],
                    'protein': row[5],
                    'carbohydrate': row[6],
                    'image':row[7],
                    }
            result.append(temp)
    cur.close()
    # if filename != '':
    #     file_ext = os.path.splitext(filename)[1]
    #     if file_ext not in app.config['UPLOAD_EXTENSIONS'] or \
    #             file_ext != validate_image(uploaded_file.stream):
    #         return "Invalid image", 400
    #     uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    data = {'message': 'Done', 'code': 'SUCCESS',"data":result}
    return make_response(jsonify(data), 200)

@app.route('/uploads/<filename>')
def upload(filename):
    return send_from_directory(app.config['UPLOAD_PATH'], filename)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8080)