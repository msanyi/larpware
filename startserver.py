import os
from app import app
import logging


env = os.environ.copy()

# Add or update the PYTHONIOENCODING environment variable
env['PYTHONIOENCODING'] = 'UTF-8'


class IgnoreAcknowledgePathFilter(logging.Filter):
    # def filter(self, record):
    #     return '/acknowledge' not in record.getMessage()
    def filter(self, record):
        message = record.getMessage()
        # Check for '/acknowledge' in the log message
        if '/acknowledge' in message:
            return False
        # Check for 'ic_interaction_job' in the log message
        if 'ic_interaction_job' in message:
            return False
        # If none of the above conditions are met, do not filter out the log entry
        return True


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get the logger and add the custom filter
    log = logging.getLogger('werkzeug')
    log.addFilter(IgnoreAcknowledgePathFilter())
    # Get the root logger and add the custom filter
    root_logger = logging.getLogger()
    root_logger.addFilter(IgnoreAcknowledgePathFilter())
    apscheduler_logger = logging.getLogger('apscheduler')
    apscheduler_logger.addFilter(IgnoreAcknowledgePathFilter())
    apscheduler_logger.setLevel(logging.WARNING)

    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
