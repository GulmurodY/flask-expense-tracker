import os
from website import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8001))
    app.run(debug=True, port=port, host='0.0.0.0')