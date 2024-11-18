from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import json
from typing import List, Optional
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
    inv_groups = list(set(p['InvGroup'] for p in products if p.get('InvGroup')))
    BrandCodes = list(set(p['BrandCode'] for p in products if p.get('BrandCode')))
    
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
    
    for cat in categories:
        html += f'<option value="{cat}">{cat}</option>'
    
    html += """
                    </select>
                    <select name="inv_group">
                        <option value="">Seleccione Grupo de Inventario</option>
    """
    
    for inv in inv_groups:
        html += f'<option value="{inv}">{inv}</option>'
    
    html += """
                    </select>
                    <select name="BrandCode">
                        <option value="">Seleccione Marca</option>
    """
    
    for BrandCode in BrandCodes:
        html += f'<option value="{BrandCode}">{BrandCode}</option>'
    
    html += """
                    </select>
                    <input type="number" name="min_price" step="0.01" placeholder="Precio mínimo" />
                    <input type="number" name="max_price" step="0.01" placeholder="Precio máximo" />
                    <input type="checkbox" name="in_stock" /> Solo en stock
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
    category: str = "all",
    min_price: Optional[str] = None,
    max_price: Optional[str] = None,
    in_stock: Optional[bool] = None,
    inv_group: Optional[str] = None,
    BrandCode: Optional[str] = None
):
    products = load_products()
    
    # Convertir min_price y max_price a float si son válidos
    try:
        min_price = float(min_price) if min_price else None
    except ValueError:
        min_price = None

    try:
        max_price = float(max_price) if max_price else None
    except ValueError:
        max_price = None

    filtered_products = []
    
    for p in products:
        # Comprobar términos de búsqueda, categoría y grupo de inventario
        if search_term.lower() not in p['Description'].lower() and search_term.lower() not in p.get('BrandCode', '').lower():
            continue
        if category != 'all' and p.get('ProductLineDesc') != category:
            continue
        if inv_group and p.get('InvGroup') != inv_group:
            continue
        if BrandCode and p.get('BrandCode') != BrandCode:
            continue

        # Comprobar el rango de precios
        match_price = False
        for price_data in p["UOMPrices"]:
            price = price_data.get("Price", 0)
            if (min_price is None or price >= min_price) and (max_price is None or price <= max_price):
                match_price = True
                break
        if not match_price:
            continue

        # Filtrar productos en stock
        if in_stock and not any(price_data.get("ActualStock", 0) > 0 for price_data in p["UOMPrices"]):
            continue

        filtered_products.append(p)
    
    # Generar el HTML con los resultados filtrados
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
    
    for p in filtered_products:
        product_id = p.get("ProductCode")  # Asumimos que ProductCode es único para cada producto
        image_html = f'<img src="{p["ImageLink"]}" class="product-image" onerror="this.style.display=\'none\'">' if p.get("ImageLink") else ''
        html += f"""
            <tr>
                <td><a href="/product/{product_id}">{image_html}{p["Description"]}</a></td>
                <td>{p.get("BrandCode", "")}</td>
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

@app.get("/product/{product_id}", response_class=HTMLResponse)
async def product_detail(product_id: str):
    products = load_products()
    product = next((p for p in products if p.get("ProductCode") == product_id), None)
    
    if not product:
        return HTMLResponse(content="<h1>Producto no encontrado</h1>", status_code=404)

    html = f"""
    <html>
        <head>
            <title>Detalle del Producto</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1 {{ color: #333; margin-bottom: 20px; }}
                .product-image {{ max-width: 100%; height: auto; }}
                .back-link {{ display: inline-block; margin-bottom: 20px; text-decoration: none; color: #007bff; }}
                .back-link:hover {{ color: #0056b3; }}
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/filter" class="back-link">← Volver a resultados</a>
                <h1>{product["Description"]}</h1>
                <img src="{product["ImageLink"]}" alt="Imagen del producto" class="product-image" onerror="this.style.display='none'"/>
                <p><strong>Marca:</strong> {product.get("BrandCode", "N/A")}</p>
                <p><strong>Categoría:</strong> {product.get("ProductLineDesc", "N/A")}</p>
                <p><strong>Grupo:</strong> {product.get("InvGroup", "N/A")}</p>
                <p><strong>Precio:</strong> €{product["SelectedUOMPrice"]["Price"]:.2f}</p>
                <p><strong>Stock:</strong> {product["SelectedUOMPrice"]["Stock"]}</p>
                <p><strong>Descripción completa:</strong> {product.get("OpriLongDescription", "N/A")}</p>
            </div>
        </body>
    </html>
    """
    
    return html

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

