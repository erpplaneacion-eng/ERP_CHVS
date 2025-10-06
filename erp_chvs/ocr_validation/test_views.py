"""
Vista de prueba simple para debugging
"""
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def test_dashboard(request):
    """Vista de prueba simple"""
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Dashboard</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <h1>🧪 Test Dashboard</h1>
            <p>Si ves esto, el servidor Django está funcionando correctamente.</p>
            <div class="alert alert-success">
                <strong>✅ Estado:</strong> Servidor operativo<br>
                <strong>👤 Usuario:</strong> """ + str(request.user) + """<br>
                <strong>🔗 URL:</strong> """ + request.path + """<br>
                <strong>📱 Método:</strong> """ + request.method + """
            </div>
            <a href="/ocr_validation/dashboard-dataframes/" class="btn btn-primary">Ir al Dashboard Real</a>
        </div>
    </body>
    </html>
    """)