class Sensor():
    """
    Klasse für den Status der Farbsensoren.
    
    Es sind lila, blau, grün, gelb, orange und terracotta verfügbar.
    """
    def __init__ (self):
        self.farbe : str = ""
    
    def farbe_ändern (self, farbe):
        """
        Eingeben einer neuen Farbe für das Programm
        
        Parameters:
        farbe (str): Farbe des Sensors
        
        Returns:
        None
        """
        try:
            farbe = str(farbe)
        except:
            None
        if (farbe == "lila"):
            self.farbe = "lila"
        if (farbe == "blau"):
            self.farbe = "blau"
        if (farbe == "grün"):
            self.farbe = "grün"
        if (farbe == "gelb"):
            self.farbe = "gelb"
        if (farbe == "orange"):
            self.farbe = "orange"
        if (farbe == "terracotta"):
            self.farbe = "terrcotta"
        else:
            self.farbe = ""
        
    def farbe_ändern_ovrd (self, farbe):
        """
        Eingeben einer neuen Farbe für das Programm
        
        Parameters:
        farbe (str): Farbe des Sensors
        
        Returns:
        None
        """
        try:
            farbe = str(farbe)
        except:
            None
            
        self.farbe = farbe

