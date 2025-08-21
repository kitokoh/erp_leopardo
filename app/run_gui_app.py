import logging
# from pyvirtualdisplay import Display

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# log.info("Starting virtual display...")
# # The 'visible=0' argument makes the display headless.
# # The size can be adjusted if needed.
# display = Display(visible=0, size=(1920, 1080))
# display.start()
# log.info("Virtual display started.")

def start_app():
    try:
        log.info("Importing and running main_crm.main()...")
        from .main_crm import main as crm_main
        crm_main()
        log.info("main_crm.main() finished.")
    except Exception as e:
        log.error(f"An error occurred while running the application: {e}", exc_info=True)
    finally:
        pass
        # log.info("Stopping virtual display.")
        # display.stop()
        # log.info("Virtual display stopped.")

if __name__ == "__main__":
    start_app()
