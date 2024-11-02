import logging
import logging.config
import os

# Ensure the log directories exist
os.makedirs('logs', exist_ok=True)

logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        },
    },
    'handlers': {
        'console': {  # Corrected name
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'DEBUG',
        },
        'file_database': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/database.log',
            'level': 'DEBUG',
        },
        'file_mint': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/mint.log',
            'level': 'DEBUG',
        },
        'file_paypal': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/paypal.log',
            'level': 'DEBUG',
        },
        'file_marketplace': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/marketplace.log',
            'level': 'DEBUG',
        },
        'file_main': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/main.log',
            'level': 'DEBUG',
        },
        'file_transaction': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/transaction.log',
            'level': 'DEBUG',
        },
        'file_storage': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/storage.log',
            'level': 'DEBUG',
        },
        'file_dac': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/dac.log',
            'level': 'DEBUG',
        },
        'file_authentication': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/authentication.log',
            'level': 'DEBUG',
        },
        
        'file_admin': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/admin.log',
            'level': 'DEBUG',
        },
        
        'file_user': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/user.log',
            'level': 'DEBUG',
        },
        
        'file_trs': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/trs.log',
            'level': 'DEBUG',
        },
        
        'file_transactions': {
            'class': 'logging.FileHandler',
            'formatter': 'standard',
            'filename': 'logs/transactions.log',
            'level': 'DEBUG',
        },
       
    },
    'loggers': {
        'database': {  # Logger for database operations
            'handlers': ['console', 'file_database'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'mint': {  # Logger for mint operations
            'handlers': ['console', 'file_mint'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'paypal': {  # Logger for PayPal operations
            'handlers': ['console', 'file_paypal'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'marketplace': {  # Logger for marketplace operations
            'handlers': ['console', 'file_marketplace'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'main': {  # Logger for main application
            'handlers': ['console', 'file_main'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'transaction': {  # Logger for transaction operations
            'handlers': ['console', 'file_transaction'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'storage':{  # Logger for transaction operations
            'handlers': ['console', 'file_transaction'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'dac':{  # Logger for transaction operations
            'handlers': ['console', 'file_dac'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        'authentication':{  # Logger for transaction operations
            'handlers': ['console', 'file_authentication'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        'admin':{  # Logger for transaction operations
            'handlers': ['console', 'file_admin'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        'user':{  # Logger for transaction operations
            'handlers': ['console', 'file_user'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        'trs':{  # Logger for transaction operations
            'handlers': ['console', 'file_trs'],
            'level': 'DEBUG',
            'propagate': False,
        },
        
        'transactions':{  # Logger for transaction operations
            'handlers': ['console', 'file_transactions'],
            'level': 'DEBUG',
            'propagate': False,
        },

    }
}

# Apply logging configuration
logging.config.dictConfig(logging_config)

