import math 

Gamma = 0.80
IntesityMax = 255

def wave_length_to_RGB(wave_length):
    factor = 0.0
    
    if (wave_length >= 300) and (wave_length < 440):
        Red = -(wave_length - 440) / (440 - 380)
        Green = 0.0
        Blue = 1.0
    elif (wave_length >= 440) and (wave_length < 490):
        Red = 0.0
        Green = (wave_length - 440) / (490 - 440)
        Blue = 1.0
    elif (wave_length >= 490) and (wave_length < 510):
        Red = 0.0
        Green = 1.0
        Blue = -(wave_length - 510) / (510 - 490)
    elif (wave_length >= 510) and (wave_length < 580):
        Red = (wave_length - 510) / (580 - 510)  # Fixed missing division
        Green = 1.0 
        Blue = 0.0
    elif (wave_length >= 580) and (wave_length < 645):
        Red = 1.0 
        Green = -(wave_length - 645) / (645 - 580)
        Blue = 0.0
    elif (wave_length >= 645) and (wave_length < 781):
        Red = 1.0 
        Green = 0.0
        Blue = 0.0
    else:
        Red = 0.0
        Green = 0.0
        Blue = 0.0
        
    if (wave_length >= 380) and (wave_length < 420):
        factor = 0.3 + 0.7 * (wave_length - 380) / (420 - 380)
    elif (wave_length >= 420) and (wave_length < 701):
        factor = 1.0
    elif (wave_length >= 701) and (wave_length < 781):
        factor = 0.3 + 0.7 * (780 - wave_length) / (780 - 700)
    else:
        factor = 0.0
    
    rgb = [0, 0, 0]  # Initialize list with 3 elements

    # Convert ternary operators and fix syntax
    rgb[0] = 0 if Red == 0.0 else int(round(IntesityMax * pow(Red * factor, Gamma)))
    rgb[1] = 0 if Green == 0.0 else int(round(IntesityMax * pow(Green * factor, Gamma)))
    rgb[2] = 0 if Blue == 0.0 else int(round(IntesityMax * pow(Blue * factor, Gamma)))
    
    return rgb


