from imapclient import IMAPClient

from inbox.basicauth import ConnectionError, ValidationError
from inbox.log import get_logger
from socket import gaierror, error as socket_error
from ssl import SSLError
log = get_logger()


def connect_account(account, host):
    """Provide a connection to a generic IMAP account.

    Raises
    ------
    ConnectionError
        If we cannot connect to the IMAP host.
    ValidationError
        If the credentials are invalid.
    """
    try:
        conn = IMAPClient(host, use_uid=True, ssl=True)
    except IMAPClient.Error as e:
        log.error('account_connect_failed',
                  host=host,
                  error="[ALERT] Can't connect to host (Failure)")
        raise ConnectionError(str(e))
    except gaierror as e:
        log.error('account_connect_failed',
                  host=host,
                  error="[ALERT] Name resolution faiure (Failure)")
        raise ConnectionError(str(e))
    except socket_error as e:
        log.error('account_connect_failed',
                  host=host,
                  error="[ALERT] Socket connection failure (Failure)")
        raise ConnectionError(str(e))

    conn.debug = False
    try:
        conn.login(account.email_address, account.password)
    except IMAPClient.Error as e:
        log.error('account_verify_failed',
                  email=account.email_address,
                  host=host,
                  error="[ALERT] Invalid credentials (Failure)")
        raise ValidationError()
    except SSLError as e:
        log.error('account_verify_failed',
                  email=account.email_address,
                  host=host,
                  error="[ALERT] SSL Connection error (Failure)")
        raise ConnectionError(str(e))

    return conn


def verify_account(account, host):
    """Verifies a generic IMAP account by logging in and logging out.

    Note: Raises exceptions from connect_account() on error.

    Returns
    -------
    True: If the client can successfully connect.
    """
    conn = connect_account(account, host)
    conn.logout()
    return True
