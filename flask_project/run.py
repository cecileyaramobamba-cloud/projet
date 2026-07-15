import os
from app import create_app

# Initialisation de l'application Flask via la factory
app = create_app()

if __name__ == "__main__":
    # Détection automatique de l'environnement (développement ou production)
    # Par défaut, il se lance en mode debug si rien n'est spécifié
    env_debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")

    # Lancement du serveur local
    # use_reloader=False : évite qu'un antivirus/EDR bloquant la création de
    # sous-processus n'empêche le vrai bind du port pendant que le terminal
    # affiche quand même "Running on http://127.0.0.1:5000".
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=env_debug,
        use_reloader=False
    )