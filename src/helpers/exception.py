class SpotinstClientException(Exception):
    def __init__(self, message, response):
        self.message = message + "\n" + response
        # Call the base class constructor with the parameters it needs
        super(SpotinstClientException, self).__init__(message)