class Hindernis():
    def __init__(self,x,y,art):
        self.typ = art # möglich sind Baum, Berg, Busch
        self.x = x
        self.y = y

    def ist_passierbar(self):
        return False