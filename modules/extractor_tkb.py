import pandas as pd
import pdfplumber
import time
import re
import xlsxwriter

def clean_header(text):
    return str(text).lower().replace('\n', '').replace(' ', '') if text else ""

def run(pdf_paths, output_path, update_status):
    teacher_data = {}
    col_keys = ['ST2', 'CT2', 'ST3', 'CT3', 'ST4', 'CT4', 'ST5', 'CT5', 'ST6', 'CT6', 'ST7', 'CT7']
    total_pages = sum(len(pdfplumber.open(p).pages) for p in pdf_paths)
    current_page = 0
    
    for path in pdf_paths:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                current_page += 1
                progress = int((current_page / total_pages) * 100)
                update_status(progress, f'Đang phân tích TKB trang {current_page}/{total_pages}...', current_page, total_pages)
                
                text = page.extract_text()
                if not text: continue
                
                cb_match = re.search(r'Cán bộ giảng dạy:\s*([^\n\(]+)', text)
                page_teacher_name = cb_match.group(1).strip() if cb_match else ""
                
                tables = page.extract_tables()
                if not tables: continue
                    
                for table in tables:
                    header_idx, thu_idx, tiet_idx, phong_idx, cbgv_idx = -1, -1, -1, -1, -1
                    for r_idx, row in enumerate(table):
                        cleaned_row = [clean_header(c) for c in row if c]
                        if any('thứ' in c for c in cleaned_row):
                            header_idx = r_idx
                            for c_i, cell in enumerate(row):
                                cl_cell = clean_header(cell)
                                if 'thứ' in cl_cell: thu_idx = c_i
                                elif 'tiếthọc' in cl_cell or 'tiếtdạy' in cl_cell: tiet_idx = c_i
                                elif 'phòng' in cl_cell: phong_idx = c_i
                                elif 'cánbộgiảngdạy' in cl_cell or 'giảngviên' in cl_cell: cbgv_idx = c_i
                            break
                            
                    if header_idx != -1 and thu_idx != -1 and tiet_idx != -1 and phong_idx != -1:
                        for r_idx in range(header_idx + 1, len(table)):
                            row = table[r_idx]
                            if len(row) <= max(thu_idx, tiet_idx, phong_idx): continue
                            thu_str = str(row[thu_idx]).strip()
                            if not thu_str.isdigit(): continue
                                
                            tiet_str = str(row[tiet_idx]).strip()
                            phong_str = str(row[phong_idx]).replace('\n', ' ').strip()
                            
                            current_teacher = str(row[cbgv_idx]).strip().replace('\n', ' ') if (cbgv_idx != -1 and len(row) > cbgv_idx and row[cbgv_idx]) else page_teacher_name
                            if not current_teacher: continue
                                
                            match = re.search(r'\d', tiet_str)
                            if match:
                                first_digit_index = match.start()
                                buoi = "ST" if first_digit_index < 6 else "CT"
                                col_name = f"{buoi}{thu_str}"
                                
                                if col_name in col_keys:
                                    if current_teacher not in teacher_data: teacher_data[current_teacher] = {k: [] for k in col_keys}
                                    if phong_str not in teacher_data[current_teacher][col_name]:
                                        teacher_data[current_teacher][col_name].append(phong_str)
                time.sleep(0.01)

    all_rows = []
    stt = 1
    for teacher, schedule in teacher_data.items():
        parts = teacher.split()
        ten = parts[-1] if len(parts) > 0 else ""
        ho_dem = " ".join(parts[:-1]) if len(parts) > 1 else ""
        row_dict = {'STT': stt, 'Họ đệm': ho_dem, 'Tên': ten}
        for k in col_keys: row_dict[k] = "\n".join(schedule[k]) if schedule[k] else ""
        all_rows.append(row_dict)
        stt += 1

    if all_rows:
        # Lưu Excel định dạng chuẩn
        workbook = xlsxwriter.Workbook(output_path)
        worksheet = workbook.add_worksheet('Data')
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'})
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        name_format = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})

        worksheet.merge_range('A1:O1', 'LỊCH BẬN CỦA GIẢNG VIÊN HỌC KỲ 1 (NĂM HỌC 2026 - 2027)', title_format)
        headers = ['TT', 'HỌ VÀ TÊN', '', 'ST2', 'CT2', 'ST3', 'CT3', 'ST4', 'CT4', 'ST5', 'CT5', 'ST6', 'CT6', 'ST7', 'CT7']
        for col_num, value in enumerate(headers):
            if value not in ['HỌ VÀ TÊN', '']: worksheet.write(1, col_num, value, header_format)
        worksheet.merge_range('B2:C2', 'HỌ VÀ TÊN', header_format)
        worksheet.set_column('A:A', 5); worksheet.set_column('B:B', 15); worksheet.set_column('C:C', 8); worksheet.set_column('D:O', 13)

        for row_idx, row_dict in enumerate(all_rows):
            row_num = row_idx + 2
            worksheet.write(row_num, 0, row_dict.get('STT', ''), cell_format)
            worksheet.write(row_num, 1, row_dict.get('Họ đệm', ''), name_format)
            worksheet.write(row_num, 2, row_dict.get('Tên', ''), name_format)
            for c_idx, key in enumerate(col_keys):
                worksheet.write(row_num, 3 + c_idx, row_dict.get(key, ''), cell_format)
        workbook.close()
        
        df = pd.DataFrame(all_rows, columns=['STT', 'Họ đệm', 'Tên'] + col_keys)
        return {
            "success": True,
            "preview": {"headers": df.columns.tolist(), "data": df.fillna('').head(50).values.tolist(), "rows": len(df), "cols": len(df.columns)}
        }
    return {"success": False, "error": "Không tìm thấy cấu trúc TKB trong PDF!"}