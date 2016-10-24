
class SimpleResult():
    code = 0
    message = ""
    def __init__(self, code , message):
        self.code = code
        self.message = message
    
    def json(self):
        return {"code":self.code,"message":self.message}

    

