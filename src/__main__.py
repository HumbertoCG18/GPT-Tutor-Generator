import logging
import sys
from src.ui.app import App

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    
    # Validação rápida de ambiente (opcional, pode ser expandida no futuro)
    if sys.version_info < (3, 8):
        logging.error("O Academic Tutor Repo Builder requer Python 3.8 ou superior.")
        sys.exit(1)

    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
