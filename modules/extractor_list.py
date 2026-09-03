import pandas as pd
import pdfplumber
import time

def run(pdf_paths, output_path, update_status):
    all_data = []
    total_pages = 0
    for p in pdf_paths:
        with pdfplumber.open(p) as pdf:
            total_pages += len(pdf.pages)
    current_page = 0
    
    for path in pdf_paths:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                current_page += 1
                progress = int((current_page / total_pages) * 100)
                update_status(progress, f'Đang trích xuất bảng trang {current_page}/{total_pages}...', current_page, total_pages)
                
                tables = page.extract_tables()
                for table in tables:
                    if table:
                        df = pd.DataFrame(table)
                        if len(df) > 0:
                            header = df.iloc[0]
                            df.columns = header
                            df = df[1:]
                            df = df.dropna(how='all')
                            if not df.empty:
                                all_data.append(df)
                time.sleep(0.01)
                
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Lưu Excel
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            final_df.to_excel(writer, sheet_name='Data', index=False)
            
        return {
            "success": True,
            "preview": {
                "headers": final_df.columns.tolist(),
                "data": final_df.fillna('').head(50).values.tolist(),
                "rows": len(final_df), "cols": len(final_df.columns)
            }
        }
    return {"success": False, "error": "Không tìm thấy dữ liệu bảng trong PDF!"}