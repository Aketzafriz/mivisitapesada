from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import json
from typing import List
from pathlib import Path

app = FastAPI()

# Configuración de directorios
PRODUCT_DATA_DIR = 'product_data'
BASE_DIR = Path(__file__).resolve().parent

def load_products() -> List[dict]:
    """Cargar todos los productos desde los archivos JSON"""
    all_products = []
    product_dir = BASE_DIR / PRODUCT_DATA_DIR
    
    if product_dir.exists():
        for file in product_dir.glob("*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if 'products' in data and 'Items' in data['products']:
                        all_products.extend(data['products']['Items'])
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Error loading {file}: {e}")
                continue
    return all_products

@app.get("/", response_class=HTMLResponse)
async def home():
    products = load_products()
    categories = ['all'] + list(set(p['ProductLineDesc'] for p in products if p.get('ProductLineDesc')))
    
    html = """
    <html>
        <head>
            <title>Catálogo de Productos</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                form {
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }
                input, select, button {
                    padding: 8px 12px;
                    margin: 5px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
                button {
                    background-color: #007bff;
                    color: white;
                    border: none;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #0056b3;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Catálogo de Productos</h1>
                <form action="/filter" method="get">
                    <input type="text" name="search_term" placeholder="Buscar productos..." />
                    <select name="category">
    """
    
    # Agregar las opciones de categoría
    for cat in categories:
        html += f'<option value="{cat}">{cat}</option>'
    
    html += """
                    </select>
                    <button type="submit">Filtrar</button>
                </form>
            </div>
        </body>
    </html>
    """
    return html

@app.get("/filter", response_class=HTMLResponse)
async def filter_products(
    search_term: str = "",
    category: str = "all"
):
    products = load_products()
    
    # Filtrar productos
    filtered_products = [
        p for p in products
        if (search_term.lower() in p['Description'].lower() or 
            search_term.lower() in p.get('Brand', '').lower()) and
        (category == 'all' or p.get('ProductLineDesc') == category)
    ]
    
    # Crear la tabla HTML
    html = """
    <html>
        <head>
            <title>Resultados de Búsqueda</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                table {
                    border-collapse: collapse;
                    width: 100%;
                    margin-top: 20px;
                }
                th, td {
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }
                th {
                    background-color: #f8f9fa;
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                .back-link {
                    display: inline-block;
                    margin-bottom: 20px;
                    text-decoration: none;
                    color: #007bff;
                }
                .back-link:hover {
                    color: #0056b3;
                }
                .product-image {
                    max-width: 50px;
                    max-height: 50px;
                    margin-right: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Resultados de Búsqueda</h1>
                <a href="/" class="back-link">← Volver</a>
                <table>
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Marca</th>
                            <th>Categoría</th>
                            <th>Grupo</th>
                            <th>Precio</th>
                            <th>Stock</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Agregar filas de productos
    for p in filtered_products:
        image_html = f'<img src="{p["ImageLink"]}" class="product-image" onerror="this.style.display=\'none\'">' if p.get("ImageLink") else ''
        html += f"""
            <tr>
                <td>{image_html}{p["Description"]}</td>
                <td>{p.get("Brand", "")}</td>
                <td>{p.get("ProductLineDesc", "")}</td>
                <td>{p.get("InvGroup", "")}</td>
                <td>€{p["SelectedUOMPrice"]["Price"]:.2f}</td>
                <td>{p["SelectedUOMPrice"]["Stock"]}</td>
            </tr>
        """
    
    html += """
                    </tbody>
                </table>
            </div>
        </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
