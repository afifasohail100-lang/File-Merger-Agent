


import os
import json
import tempfile
import sys
from flask import Flask, request, render_template, send_file, jsonify
from werkzeug.utils import secure_filename

# Add current directory to Python path (helps with imports)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import local modules
try:
    import pdf_processor
    import word_generator
    import database  # if running as module
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Current directory:", os.getcwd())
    print("Files in directory:", os.listdir('.'))
    sys.exit(1)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database
try:
    database.create_tables()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"❌ Database initialization error: {e}")

@app.route('/')
def index():
    """Home page with upload form."""
    return render_template('upload.html')

@app.route('/convert', methods=['POST'])
def convert_pdfs():
    """Convert uploaded PDFs to merged Word document."""
    if 'files' not in request.files:
        return 'No files uploaded', 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return 'No files selected', 400
    
    converted_books = []
    temp_files = []
    
    try:
        # Process each PDF
        for file in files:
            if file and file.filename.endswith('.pdf'):
                filename = secure_filename(file.filename)
                
                # Save temporarily
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
                file.save(temp_path)
                temp_files.append(temp_path)
                
                # Convert to JSON
                print(f"🔄 Converting: {filename}")
                book_data = pdf_processor.pdf_to_json(temp_path, title=os.path.splitext(filename)[0])
                converted_books.append(book_data)
                
                # Save to database
                try:
                    book_id = database.save_book(book_data)
                    print(f"✅ Saved '{book_data['title']}' to database with ID: {book_id}")
                except Exception as db_error:
                    print(f"⚠️ Database save error (continuing anyway): {db_error}")
        
        if not converted_books:
            return 'No valid PDF files were converted', 400
        
        # Merge all books
        print(f"🔄 Merging {len(converted_books)} books...")
        merged_data = pdf_processor.merge_books(converted_books)
        
        # Save merged data to database (if possible)
        try:
            merge_id = database.save_merged_books(merged_data)
            print(f"✅ Saved merged collection to database with ID: {merge_id}")
        except Exception as db_error:
            print(f"⚠️ Database save error for merged data: {db_error}")
        
        # Create Word document
        print("🔄 Creating Word document...")
        output_filename = os.path.join(app.config['UPLOAD_FOLDER'], 'merged_books.docx')
        word_generator.create_word_document(merged_data, output_filename)
        
        print("✅ Conversion complete!")
        
        # Send the Word document
        return send_file(
            output_filename,
            as_attachment=True,
            download_name='merged_books.docx',
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return str(e), 500
    
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"🧹 Cleaned up: {temp_file}")
            except:
                pass

@app.route('/database-view')
def view_database():
    """View database contents."""
    try:
        books = database.get_all_books()
        return render_template('database_view.html', books=books)
    except Exception as e:
        return f"Error viewing database: {e}", 500

@app.route('/export-database')
def export_database():
    """Export entire database as JSON."""
    try:
        books = database.get_all_books()
        
        # Get full data for each book
        data = []
        for book in books:
            book_data = database.get_book_by_id(book['id'])
            if book_data:
                data.append(book_data)
        
        return jsonify({
            "total_books": len(data),
            "books": data,
            "export_date": __import__("datetime").datetime.now().isoformat()
        })
    except Exception as e:
        return f"Error exporting database: {e}", 500

@app.route('/view-book/<int:book_id>')
def view_book(book_id):
    """View a specific book."""
    try:
        book_data = database.get_book_by_id(book_id)
        if book_data:
            return jsonify(book_data)
        return "Book not found", 404
    except Exception as e:
        return f"Error viewing book: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)