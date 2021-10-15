import math

# py -c 'import dataPredication; dataPredication.getVDOT(1000, 255.0)'
def getVDOT(distance, time):
    # Swap time to minutes
    time = time / 60.0
    velocity = distance / time
    o2cost = 0.182258 * velocity + 0.000104 * velocity**2 - 4.60
    # This is the profile of an elite athlete, which I am not
    dropdead = 0.2989558 * math.exp(-0.1932605 * time) + 0.1894393 * math.exp(-0.012778 * time) + 0.8
    VDOT = o2cost / dropdead
    print(VDOT)

