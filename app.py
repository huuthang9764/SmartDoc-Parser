import sys
import os
import threading
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename

# Nhúng các chuyên viên (Modules) từ thư mục modules
from modules import extractor_tkb, extractor_list

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN (Hỗ trợ cả Code và file .EXE)
# ==========================================
if getattr(sys, 'frozen', False):
    # Nếu đang chạy bằng file .exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Nếu đang chạy bằng mã nguồn .py thông thường
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Khởi tạo Flask và chỉ định rõ thư mục giao diện
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, 'templates'))
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# Tạo thư mục chứa file xuất ra nằm ngay cạnh file .exe
OUTPUT_DIR = os.path.join(BASE_DIR, 'data_output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.config['UPLOAD_FOLDER'] = OUTPUT_DIR

ALLOWED_EXTENSIONS = {'pdf'}

# ==========================================
# BẢN ĐỒ CÔNG CỤ & BIẾN TRẠNG THÁI
# ==========================================
# Kết nối Mode từ Web với Module xử lý tương ứng
TOOLS = {
    'tkb': extractor_tkb.run,
    'list': extractor_list.run
}

# Biến toàn cục giao tiếp với Web
processing_status = {'status': 'idle', 'progress': 0, 'message': '', 'current_page': 0, 'total_pages': 0}
preview_data = {'headers': [], 'data': [], 'rows': 0, 'cols': 0}
current_file_info = {'base_name': 'Ket_Qua'}

# Hàm Callback để Modules báo cáo tiến độ về cho app
def update_status(progress, message, current_page, total_pages):
    global processing_status
    processing_status.update({
        'progress': progress, 'message': message, 
        'current_page': current_page, 'total_pages': total_pages
    })

# ==========================================
# CÁC ROUTE GIAO TIẾP VỚI GIAO DIỆN WEB
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global processing_status, preview_data, current_file_info
    
    files = request.files.getlist('files[]')
    mode = request.form.get('mode', 'tkb')
    
    if not files or files[0].filename == '': 
        return jsonify({'error': 'Chưa chọn file nào'}), 400
    if mode not in TOOLS: 
        return jsonify({'error': 'Chức năng không tồn tại'}), 400
    
    try:
        # Reset dữ liệu cũ
        preview_data = {'headers': [], 'data': [], 'rows': 0, 'cols': 0}
        update_status(0, 'Đang chuẩn bị dữ liệu...', 0, 0)
        processing_status['status'] = 'processing'
        
        # Tạo tên file gợi ý khi tải về
        first_name = os.path.splitext(secure_filename(files[0].filename))[0]
        current_file_info['base_name'] = first_name if len(files) == 1 else f"{first_name}_Gop_{len(files)}_File"
        
        # Lưu các file PDF tải lên vào thư mục output tạm
        pdf_paths = []
        for file in files:
            path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))
            file.save(path)
            pdf_paths.append(path)
            
        def process_thread():
            global processing_status, preview_data
            try:
                output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_data.xlsx')
                
                # Gọi ĐÚNG Module xử lý dựa theo tên Tool
                processor_func = TOOLS[mode]
                result = processor_func(pdf_paths, output_path, update_status)
                
                if result['success']:
                    preview_data = result['preview']
                    processing_status['status'] = 'done'
                    update_status(100, 'Xử lý hoàn tất!', processing_status['total_pages'], processing_status['total_pages'])
                else:
                    processing_status['status'] = 'error'
                    update_status(0, result['error'], 0, 0)
                    
            except Exception as e:
                processing_status['status'] = 'error'
                update_status(0, f'Lỗi hệ thống: {str(e)}', 0, 0)
            finally:
                # Xóa dọn các file PDF rác sau khi phân tích xong
                for path in pdf_paths:
                    if os.path.exists(path): 
                        try:
                            os.remove(path)
                        except:
                            pass
                    
        # Chạy phân tích trong một luồng (thread) riêng để không làm đơ trang web
        threading.Thread(target=process_thread).start()
        return jsonify({'status': 'processing'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status')
def get_status(): 
    return jsonify(processing_status)

@app.route('/preview')
def get_preview():
    if not preview_data['headers']: 
        return jsonify({'success': False})
    return jsonify({'success': True, **preview_data})

@app.route('/download')
def download_file():
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted_data.xlsx')
    if not os.path.exists(output_path): 
        return jsonify({'error': 'Chưa có file'}), 404
        
    requested_name = request.args.get('filename', f"{current_file_info['base_name']}.xlsx")
    if not requested_name.endswith('.xlsx'): 
        requested_name += '.xlsx'
        
    return send_file(
        output_path, 
        as_attachment=True, 
        download_name=requested_name, 
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    # Bật server ở cổng 5000
    app.run(debug=False, host='0.0.0.0', port=5000)