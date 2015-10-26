import pyaudio, wave, sys, math, struct
from Tkinter import *
import eventBasedAnimation
from pydub import AudioSegment
from pydub.playback import play

################################################################################
# misc helper functions
################################################################################

def changePitch(pitch, octave, delta):
    scale = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    if (pitch == 'C') and (octave == 1) and (delta == -1):
        return (pitch, octave)
    elif (pitch == 'B') and (octave == 7) and (delta == 1):
        return (pitch, octave)
    newIndex = scale.index(pitch) + delta
    if newIndex >= len(scale):
        octave += 1
        newIndex = newIndex % len(scale)
    elif newIndex < 0:
        octave -= 1
        newIndex = newIndex % len(scale)
    return (scale[newIndex], octave)

def changeRhythm(duration, delta):
    rhythm = [.125, .25, .375, .5, .75, 1.0, 1.5, 2.0, 3.0, 4.0]
    #        [32nd, 16th,d16th, 8th,d8th,4th, d4th,2nd,d2nd,whole]
    assert (duration in rhythm)
    newIndex = (rhythm.index(duration) + delta) % len(rhythm)
    return rhythm[newIndex]

def loadClefImages():
    global listOfClefs
    listOfClefs = []
    clefs = ['treble', 'alto', 'bass']
    for clef in clefs:
        filename = 'clefs/%s.gif' % (clef)
        listOfClefs.append(PhotoImage(file=filename))
# adapted from course notes: 
# cs.cmu.edu/~112/notes/notes-event-based-animations.html

def loadClefImagesBecauseTkinterIsStupid():
    global TkinterSucks
    TkinterSucks = []
    clefs = ['treble', 'alto', 'bass']
    for clef in clefs:
        filename = 'clefsForStartMenu/%s.gif' % (clef)
        TkinterSucks.append(PhotoImage(file=filename))
# adapted from course notes: 
# cs.cmu.edu/~112/notes/notes-event-based-animations.html

def positionClef(index, x, y):
    if index == 0:
        return (x + 15, y + 23)
    elif index == 1:
        return (x + 17, y + 20)
    elif index == 2:
        return (x + 17, y + 21)
# helper function for positioning clefs

def positionNote(clef, pitch, octave, top, distance):
    note = pitch + str(octave)
    index = returnNoteIndex(pitch, octave)
    if clef == 0:
        topLineIndex = 155
    elif clef == 1:
        topLineIndex = 125
    else:
        topLineIndex = 95
    return topLineIndex - (distance/2) * index

def obtainNoteFromPosition(clef, y):
    if clef == 0:
        topLineIndex = 31
    elif clef == 1:
        topLineIndex = 25
    else:
        topLineIndex = 19
    index = topLineIndex - int((y + 2.5)/5)
    (pitch, octave) = returnNote(index)
    return (pitch, octave)

def returnNoteIndex(pitch, octave):
    noteString = pitch + str(octave)
    notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    fullRange = []
    for octave in xrange(1, 8):
        for note in notes:
            fullRange += [note + str(octave)]
    return fullRange.index(noteString)

def returnNote(index):
    notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    fullRange = []
    for octave in xrange(1, 8):
        for note in notes:
            fullRange += [note + str(octave)]
    noteString = fullRange[index]
    return (noteString[0], int(noteString[1]))

def deselectAll(data):
    for staff in data.score[data.page].staves:
        for measure in staff.measures:
            for item in measure.notes:
                item.selected = False

def deremoveAll(data):
    for staff in data.score[data.page].staves:
        for measure in staff.measures:
            for item in measure.notes:
                item.removed = False

def obtainFileName(pitch, octave, accidental):
    notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    if accidental == '':
        return pitch + str(octave)
    elif accidental == 'f':
        if pitch == 'C':
            return 'B' + str(octave - 1)
        elif pitch == 'F':
            return 'E' + str(octave)
        else:
            return pitch + 'b' + str(octave)
    else:
        if pitch == 'E':
            return 'F' + str(octave)
        elif pitch == 'B':
            return 'C' + str(octave + 1)
        else:
            newIndex = notes.index(pitch) + 1
            return notes[newIndex] + 'b' + str(octave)

def generateAudioDictionary():
    audioDictionary = dict()
    scale = ['C','Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
    for octave in xrange(1, 8):
        for pitch in scale:
            fileName = pitch + str(octave)
            audio = AudioSegment.from_wav('notes/%s.wav' % (fileName))
            audioDictionary[fileName] = audio
    rest = AudioSegment.from_wav('notes/rest.wav')
    audioDictionary['rest'] = rest
    return audioDictionary

def writeFile(data, mode='wt'):
    fileName = data.fileName.get()
    contents = str(data.clef)+'\n'+str(data.timeTop)+'\n'+str(data.timeBot)+'\n'
    for pageI in xrange(len(data.score)):
        currentPage = data.score[pageI]
        for staffI in xrange(len(currentPage.staves)):
            currentStaff = currentPage.staves[staffI]
            for measureI in xrange(len(currentStaff.measures)):
                currentMeasure = currentStaff.measures[measureI]
                if len(currentMeasure.notes) > 0:
                    contents += '('+str(pageI)+','+str(staffI)+','+str(measureI)+')'+'\n'
                    contents += repr(currentMeasure.notes)+'\n'
    with open(fileName, mode) as fileText:
        fileText.write(contents)

def loadData(data, fileName, mode='rt'):
    with open(fileName, mode) as fileText:
        contents = fileText.read()
    contentList = contents.splitlines()
    data.clef = eval(contentList[0])
    data.timeTop = eval(contentList[1])
    data.timeBot = eval(contentList[2])

def loadNotes(data, fileName, mode='rt'):
    with open(fileName, mode) as fileText:
        contents = fileText.read()
    contentList = contents.splitlines()
    if len(contentList) > 3 and contentList[3] != '\n':
        for i in xrange(3, len(contentList), 2):
            (pageI, staffI, measureI) = eval(contentList[i])
            notesList = eval(contentList[i+1])
            try:
                data.score[pageI].staves[staffI].measures[measureI].notes = notesList
            except:
                for j in xrange(pageI):
                    data.score.append(Page(data.clef, data.timeTop, data.timeBot))
                data.score[pageI].staves[staffI].measures[measureI].notes = notesList


################################################################################
# helper functions for drawing notes:
################################################################################

def drawNote(canvas, x, y, r, c, duration, stemDirection, stemLength):
    if duration == .125:
        # draws 32nd note
        draw32nd(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == .25:
        # draws 16th note
        draw16th(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == .375:
        # draws dotted 16th note
        drawDotted16th(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == .5:
        # draws 8th note
        draw8th(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == .75:
        # draws dotted 8th note
        drawDotted8th(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == 1.0:
        # draws quarter note
        drawQuarter(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == 1.5:
        # draws dotted quarter note
        drawDottedQuarter(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == 2.0:
        # draws half note
        drawHalf(canvas, x, y, r, c, stemDirection, stemLength)
    elif duration == 3.0:
        # draws dotted half note
        drawDottedHalf(canvas, x, y, r, c, stemDirection, stemLength)
    else:
        # draws whole note
        drawWhole(canvas, x, y, r, c)

def draw32nd(canvas, x, y, r, c, stemDirection, stemLength):
    flag = 10
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        stemX = x + (c * r)
        stemTop = y - stemLength
        canvas.create_line(stemX, y, stemX, stemTop, width=2)
        canvas.create_line(stemX, stemTop, stemX+flag, stemTop+flag, width=2)
        canvas.create_line(stemX, stemTop+flag*.5, stemX+flag, stemTop+flag*1.5, width=2)
        canvas.create_line(stemX, stemTop+flag, stemX+flag, stemTop+flag*2, width=2)
    else:
        stemX = x - (c * r)
        stemBot = y + stemLength
        canvas.create_line(stemX, y, stemX, stemBot, width=2)
        canvas.create_line(stemX, stemBot, stemX+flag, stemBot-flag, width=2)
        canvas.create_line(stemX, stemBot-flag*.5, stemX+flag, stemBot-flag*1.5, width=2)
        canvas.create_line(stemX, stemBot-flag, stemX+flag, stemBot-flag*2, width=2)

def draw16th(canvas, x, y, r, c, stemDirection, stemLength):
    flag = 10
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        stemX = x + (c * r)
        stemTop = y - stemLength
        canvas.create_line(stemX, y, stemX, stemTop, width=2)
        canvas.create_line(stemX, stemTop, stemX+flag, stemTop+flag, width=2)
        canvas.create_line(stemX, stemTop+flag, stemX+flag, stemTop+flag*2, width=2)
    else:
        stemX = x - (c * r)
        stemBot = y + stemLength
        canvas.create_line(stemX, y, stemX, stemBot, width=2)
        canvas.create_line(stemX, stemBot, stemX+flag, stemBot-flag, width=2)
        canvas.create_line(stemX, stemBot-flag, stemX+flag, stemBot-flag*2, width=2)

def drawDotted16th(canvas, x, y, r, c, stemDirection, stemLength):
    flag = 10
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        stemX = x + (c * r)
        stemTop = y - stemLength
        canvas.create_line(stemX, y, stemX, stemTop, width=2)
        canvas.create_line(stemX, stemTop, stemX+flag, stemTop+flag, width=2)
        canvas.create_line(stemX,stemTop+flag,stemX+flag,stemTop+flag*2,width=2)
    else:
        stemX = x - (c * r)
        stemBot = y + stemLength
        canvas.create_line(stemX, y, stemX, stemBot, width=2)
        canvas.create_line(stemX, stemBot, stemX+flag, stemBot-flag, width=2)
        canvas.create_line(stemX,stemBot-flag,stemX+flag,stemBot-flag*2, width=2)
    canvas.create_text(x+1.5*(c*r), y-r, text='.',anchor=W,font='Times 18 bold')

def draw8th(canvas, x, y, r, c, stemDirection, stemLength):
    flag = 10
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        stemX = x + (c * r)
        stemTop = y - stemLength
        canvas.create_line(stemX, y, stemX, stemTop, width=2)
        canvas.create_line(stemX, stemTop, stemX+flag, stemTop+flag, width=2)
    else:
        stemX = x - (c * r)
        stemBot = y + stemLength
        canvas.create_line(stemX, y, stemX, stemBot, width=2)
        canvas.create_line(stemX, stemBot, stemX+flag, stemBot-flag, width=2)

def drawDotted8th(canvas, x, y, r, c, stemDirection, stemLength):
    flag = 10
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        stemX = x + (c * r)
        stemTop = y - stemLength
        canvas.create_line(stemX, y, stemX, stemTop, width=2)
        canvas.create_line(stemX, stemTop, stemX+flag, stemTop+flag, width=2)
    else:
        stemX = x - (c * r)
        stemBot = y + stemLength
        canvas.create_line(stemX, y, stemX, stemBot, width=2)
        canvas.create_line(stemX, stemBot, stemX+flag, stemBot-flag, width=2)
    canvas.create_text(x+1.5*(c*r), y-r, text='.',anchor=W,font='Times 18 bold')

def drawQuarter(canvas, x, y, r, c, stemDirection, stemLength):
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        canvas.create_line(x + (c * r), y, x + (c * r), y - stemLength, width=2)
    else:
        canvas.create_line(x - (c * r), y, x - (c * r), y + stemLength, width=2)

def drawDottedQuarter(canvas, x, y, r, c, stemDirection, stemLength):
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, fill='Black')
    if stemDirection == 'Up':
        canvas.create_line(x + (c * r), y, x + (c * r), y - stemLength, width=2)
    else:
        canvas.create_line(x - (c * r), y, x - (c * r), y + stemLength, width=2)
    canvas.create_text(x+1.5*(c*r), y-r, text='.',anchor=W,font='Times 18 bold')

def drawHalf(canvas, x, y, r, c, stemDirection, stemLength):
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, width=2)
    if stemDirection == 'Up':
        canvas.create_line(x + (c * r), y, x + (c * r), y - stemLength, width=2)
    else:
        canvas.create_line(x - (c * r), y, x - (c * r), y + stemLength, width=2)

def drawDottedHalf(canvas, x, y, r, c, stemDirection, stemLength):
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, width=2)
    if stemDirection == 'Up':
        canvas.create_line(x + (c * r), y, x + (c * r), y - stemLength, width=2)
    else:
        canvas.create_line(x - (c * r), y, x - (c * r), y + stemLength, width=2)
    canvas.create_text(x+1.5*(c*r), y-r, text='.',anchor=W,font='Times 18 bold')

def drawWhole(canvas, x, y, r, c):
    canvas.create_oval(x - (c * r), y - r, x + (c * r), y + r, width=2)

def drawSharp(canvas, x, y):
    (d, length, width, r, offset) = (15, 16, 10, 2.5, 2)
    (cX, cY) = (x - d, y)
    # vertical lines:
    canvas.create_line(cX-r, cY-length/2+offset, cX-r, cY+length/2+offset)
    canvas.create_line(cX+r, cY-length/2, cX+r, cY+length/2)
    # horizontal lines:
    canvas.create_line(cX-2*r, cY-r+offset, cX-2*r+width, cY-r-offset, width=3)
    canvas.create_line(cX-2*r, cY+r+offset, cX-2*r+width, cY+r-offset, width=3)

def drawFlat(canvas, x, y):
    (d, length, r) = (15, 16, 2.5)
    (cX, cY) = (x - d, y)
    canvas.create_line(cX-r, cY-length*.7, cX-r, cY+length*.3, width=2)
    canvas.create_arc(cX-r, cY-length*.15, cX+r, cY+length*.25, start=240, 
                      extent=250, style=ARC, width=2)

################################################################################
# helper functions for drawing rests:
################################################################################

def drawRest(canvas, duration, top, distance, x):
    if duration == .125:
        # draws 32nd rest
        draw32ndRest(canvas, top, distance, x)
    elif duration == .25:
        # draws 16th rest
        draw16thRest(canvas, top, distance, x)
    elif duration == .375:
        # draws dotted 16th rest
        drawDotted16thRest(canvas, top, distance, x)
    elif duration == .5:
        # draws 8th rest
        draw8thRest(canvas, top, distance, x)
    elif duration == .75:
        # draws dotted 8th rest
        drawDotted8thRest(canvas, top, distance, x)
    elif duration == 1.0:
        # draws quarter rest
        drawQuarterRest(canvas, top, distance, x)
    elif duration == 1.5:
        # draws dotted quarter rest
        drawDottedQuarterRest(canvas, top, distance, x)
    elif duration == 2.0:
        # draws half rest
        drawHalfRest(canvas, top, distance, x)
    elif duration == 3.0:
        # draws dotted half rest
        drawDottedHalfRest(canvas, top, distance, x)
    else:
        # draws whole rest
        drawWholeRest(canvas, top, distance, x)

def draw32ndRest(canvas, top, distance, x):
    x -= 5
    y = top + 1.5 * distance
    r = 2.5
    d = distance
    canvas.create_oval(x+.5*d-r, y-d-r, x+.5*d+r,   y-d+r,  fill='black')
    canvas.create_line(x+.5*d,   y-d+r, x+1.25*d,   y-d)
    canvas.create_oval(x-r,      y-r,   x+r,        y+r,    fill='black')
    canvas.create_line(x,        y+r,   x+.75*d,    y)
    canvas.create_oval(x-.5*d-r, y+d-r, x-.5*d+r,   y+d+r,  fill='black')
    canvas.create_line(x-.5*d,   y+r+d, x+.25*d,    y+d)
    canvas.create_line(x+1.25*d, y-d,   x-.25*d,    y+2.5*d)

def draw16thRest(canvas, top, distance, x):
    x -= 5
    y = top + 1.5 * distance
    r = 2.5
    d = distance
    canvas.create_oval(x-r,     y-r,    x+r,        y+r,    fill='black')
    canvas.create_line(x,       y+r,    x+.75*d,    y)
    canvas.create_oval(x-.5*d-r,y+d-r,  x-.5*d+r,   y+d+r,  fill='black')
    canvas.create_line(x-.5*d,  y+r+d,  x+.25*d,    y+d)
    canvas.create_line(x+.75*d, y,      x-.25*d,    y+2.5*d)

def drawDotted16thRest(canvas, top, distance, x):
    x -= 5
    y = top + 1.5 * distance
    r = 2.5
    d = distance
    canvas.create_oval(x-r,     y-r,    x+r,        y+r,    fill='black')
    canvas.create_line(x,       y+r,    x+.75*d,    y)
    canvas.create_oval(x-.5*d-r,y+d-r,  x-.5*d+r,   y+d+r,  fill='black')
    canvas.create_line(x-.5*d,  y+r+d,  x+.25*d,    y+d)
    canvas.create_line(x+.75*d, y,      x-.25*d,    y+2.5*d)
    # draws dot:
    (dotX, dotY, r) = (x + distance + r, top + 1.5 * distance, 1)
    canvas.create_oval(dotX-r, dotY-r, dotX+r, dotY+r, fill='Black')

def draw8thRest(canvas, top, distance, x):
    x -= 5
    y = top + 1.5 * distance
    r = 2.5
    d = distance
    canvas.create_oval(x-r,     y-r,    x+r,        y+r,    fill='black')
    canvas.create_line(x,       y+r,    x+.75*d,    y)
    canvas.create_line(x+.75*d, y,      x+.25*d,    y+1.5*d)

def drawDotted8thRest(canvas, top, distance, x):
    x -= 5
    y = top + 1.5 * distance
    r = 2.5
    d = distance
    canvas.create_oval(x-r,     y-r,    x+r,        y+r,    fill='black')
    canvas.create_line(x,       y+r,    x+.75*d,    y)
    canvas.create_line(x+.75*d, y,      x+.25*d,    y+1.5*d)
    # draws dot:
    (dotX, dotY, r) = (x + distance + r, top + 1.5 * distance, 1)
    canvas.create_oval(dotX-r, dotY-r, dotX+r, dotY+r, fill='Black')

def drawQuarterRest(canvas, top, distance, x):
    (startX, startY, d) = (x - distance/2, top + .5*distance, distance)
    canvas.create_line(startX, startY, startX+d, startY+d, width=3)
    canvas.create_line(startX+d, startY+d, startX, startY+d, width=3)
    canvas.create_line(startX, startY+d, startX+d, startY+2*d, width=3)
    (arcX, arcY) = (x - d/2, top + 2.5 * d)
    canvas.create_arc(arcX,arcY,arcX+d,arcY+d,start=50,extent=240,style=ARC,width=3)

def drawDottedQuarterRest(canvas, top, distance, x):
    (startX, startY, d) = (x - distance/2, top + .5*distance, distance)
    canvas.create_line(startX, startY, startX+d, startY+d, width=3)
    canvas.create_line(startX+d, startY+d, startX, startY+d, width=3)
    canvas.create_line(startX, startY+d, startX+d, startY+2*d, width=3)
    (arcX, arcY) = (x - d/2, top + 2.5 * d)
    canvas.create_arc(arcX,arcY,arcX+d,arcY+d,start=50,extent=240,style=ARC,width=3)
    # draws dot:
    (dotX, dotY, r) = (x + distance, top + 1.5 * distance, 1)
    canvas.create_oval(dotX-r, dotY-r, dotX+r, dotY+r, fill='Black')

def drawHalfRest(canvas, top, distance, x):
    (yTop, yBot) = (top + 1.5 * distance, top + 2 * distance)
    length = 10
    canvas.create_rectangle(x-length/2, yTop, x+length/2, yBot, fill='Black')

def drawDottedHalfRest(canvas, top, distance, x):
    (yTop, yBot) = (top + 1.5 * distance, top + 2 * distance)
    length = 10
    canvas.create_rectangle(x-length/2, yTop, x+length/2, yBot, fill='Black')
    (dotX, dotY, r) = (x + distance, top + 1.5 * distance, 1)
    canvas.create_oval(dotX-r, dotY-r, dotX+r, dotY+r, fill='Black')

def drawWholeRest(canvas, top, distance, x):
    (yTop, yBot) = (top + distance, top + 1.5 * distance)
    length = 10
    canvas.create_rectangle(x-length/2, yTop, x+length/2, yBot, fill='Black')

################################################################################
# objects
################################################################################

class Note(object):
    def __init__(self, pitch, octave, duration=1.0, accidental='', selected=False, removed=False):
        (self.pitch, self.octave, self.duration) = (pitch, octave, duration)
        self.selected = selected
        self.removed = removed
        self.accidental = accidental
        self.fileName = obtainFileName(pitch, octave, accidental)

    def __repr__(self):
        result = str(type(self).__name__) + "("
        result += '"' + self.pitch + '"' + ','
        result += str(self.octave) + ','
        result += str(self.duration) + ','
        result += '"' + self.accidental + '"' + ')'
        return result
    # from course notes:
    # http://www.cs.cmu.edu/~112/notes/notes-oop.html

    def draw(self, canvas, clef, top, distance, x):
        self.x = x
        self.y = top+positionNote(clef, self.pitch, self.octave, top, distance)
        self.r = distance/2 - 1
        self.c = 1.5                         # width multiplier to get oval note
        # select circle:
        selectR = 3.5 * self.r
        if self.selected == True:
            canvas.create_oval(x-selectR,self.y-selectR,x+selectR,self.y+selectR,
                               outline='turquoise2', width=2)
        if self.removed == True:
            canvas.create_oval(x-selectR,self.y-selectR,x+selectR,self.y+selectR,
                               outline='DeepPink2', width=2)
        # stems:
        if self.y >= top + 2 * distance:
            stem = 'Up'
        else:
            stem = 'Down'
        stemLength = 3.5 * distance
        # note:
        bot = top + 4 * distance
        if self.y < top:
            for i in xrange(10, abs(self.y-top)+1, 10):
                canvas.create_line(x-2.5*self.r, top-i, x + 2.5 * self.r, top-i)
        elif self.y > top + 4 * distance:
            for i in xrange(10, abs(self.y-bot)+1, 10):
                canvas.create_line(x-2.5*self.r, bot+i, x + 2.5 * self.r, bot+i)
        drawNote(canvas,x,self.y,self.r,self.c,self.duration,stem,stemLength)
        # accidentals:
        if self.accidental == 'f':
            drawFlat(canvas, x, self.y)
        elif self.accidental == 's':
            drawSharp(canvas, x, self.y)

    def selectTest(self, event):
        (lowerX, lowerY) = (self.x - self.r * 1.5, self.y - self.r * 1.5)
        (upperX, upperY) = (self.x + self.r * 1.5, self.y + self.r * 1.5)
        if lowerX < (event.x) < upperX and lowerY < (event.y) < upperY:
            self.selected = True
            return True
        else:
            self.selected = False
            return False

    def removeTest(self, event):
        (lowerX, lowerY) = (self.x - self.r * 1.5, self.y - self.r * 1.5)
        (upperX, upperY) = (self.x + self.r * 1.5, self.y + self.r * 1.5)
        if lowerX < (event.x) < upperX and lowerY < (event.y) < upperY:
            self.removed = True
            return True

    def changePitch(self, delta):
        (self.pitch, self.octave) = changePitch(self.pitch, self.octave, delta)
        self.fileName = obtainFileName(self.pitch, self.octave, self.accidental)

    def changeRhythm(self, delta):
        self.duration = changeRhythm(self.duration, delta)
        self.fileName = obtainFileName(self.pitch, self.octave, self.accidental)

    def changeAccidental(self, accidental):
        self.accidental = accidental
        self.fileName = obtainFileName(self.pitch, self.octave, self.accidental)

class Rest(object):
    def __init__(self, duration=1.0, selected=False, removed=False):
        self.duration = duration
        self.selected = selected
        self.removed = removed
        self.fileName = 'rest'

    def __repr__(self):
        result = str(type(self).__name__) + "("
        result += str(self.duration) + ')'
        return result

    def draw(self, canvas, top, distance, x):
        self.x = x
        self.top = top
        self.distance = distance
        if self.selected == True:
            margin = 5
            canvas.create_rectangle(self.x-distance, self.top-margin, 
                                    self.x+distance, top + 4*distance+margin, 
                                    outline='turquoise2', width=2)
        if self.removed == True:
            margin = 5
            canvas.create_rectangle(self.x-distance, self.top-margin, 
                                    self.x+distance, top + 4*distance+margin, 
                                    outline='DeepPink2', width=2)
        drawRest(canvas, self.duration, top, distance, x)

    def selectTest(self, event):
        x = self.x
        d = self.distance
        (lowerX, lowerY) = (x-d, self.top + d)
        (upperX, upperY) = (x+d, self.top + 3*d)
        if lowerX < (event.x) < upperX and lowerY < (event.y) < upperY:
            self.selected = True
            return True
        else:
            self.selected = False
            return False

    def removeTest(self, event):
        x = self.x
        d = self.distance
        (lowerX, lowerY) = (x-d, self.top + d)
        (upperX, upperY) = (x+d, self.top + 3*d)
        if lowerX < (event.x) < upperX and lowerY < (event.y) < upperY:
            self.removed = True
            return True

    def changeRhythm(self, delta):
        self.duration = changeRhythm(self.duration, delta)

class Measure(object):
    def __init__(self, clef, staffIndex, measureIndex):
        self.notes = []
        self.clef = clef
        (self.staffIndex, self.measureIndex) = (staffIndex, measureIndex)

    def draw(self, canvas, start, width, top, height, distance):
        self.start, self.width, self.top = start, width, top
        self.height, self.distance = height, distance
        end = start + width
        canvas.create_line(end, top, end, top + height)
        for i in xrange(len(self.notes)):
            xPosition = width/(len(self.notes) + 1) * (i + 1) + start
            if type(self.notes[i]) == Note:
                self.notes[i].draw(canvas, self.clef, top, distance, xPosition)
            else:
                self.notes[i].draw(canvas, top, distance, xPosition)

    def addNote(self, event):
        try:
            (lowerX, upperX) = (self.start, self.start + self.width)
            extra = 2 * self.distance
            (lowerY, upperY) = (self.top-extra, self.top+self.height+extra)
            if lowerX < event.x < upperX and lowerY < event.y < upperY:
                (pitch,octave)=obtainNoteFromPosition(self.clef,event.y-self.top)
                x = event.x - self.start
                index = int(x / (self.width / (len(self.notes) + 1)))
                self.notes.insert(index, Note(pitch, octave))
        except: pass

    def addRest(self, event):
        try:
            (lowerX, upperX) = (self.start, self.start + self.width)
            extra = 2 * self.distance
            (lowerY, upperY) = (self.top-extra, self.top+self.height+extra)
            if lowerX < event.x < upperX and lowerY < event.y < upperY:
                x = event.x - self.start
                index = int(x / (self.width / (len(self.notes) + 1)))
                self.notes.insert(index, Rest())
        except: pass

    def remove(self, item):
        if item in self.notes:
            self.notes.remove(item)

    def beatCheck(self, top, bot):
        if len(self.notes) > 0:
            totalDuration = 0
            for item in self.notes:
                totalDuration += item.duration
            c = 4.0         # constant for time signature to duration conversion
            correctDuration = top * (c / bot)
            if totalDuration != correctDuration:
                (i, j) = (self.staffIndex, self.measureIndex)
                message = 'Line '+str(i)+', Measure '+str(j)
                if totalDuration > correctDuration:
                    message += ' is too long!'
                else:
                    message += ' is too short!'
                return [message]
        return []

class Staff(object):
    def __init__(self, clef, timeTop, timeBot, staffIndex):
        self.lines = 5
        self.measureCount = 4
        self.clef = clef
        (self.timeTop, self.timeBot) = (timeTop, timeBot)
        self.measures = []
        for i in xrange(self.measureCount):
            self.measures += [Measure(self.clef, staffIndex, i + 1)]
        loadClefImages()

    def draw(self, canvas, height, left, right, top):
        # draws lines:
        distance = height/self.lines
        for line in xrange(self.lines):
            lineY = top + line * distance
            canvas.create_line(left, lineY, right, lineY)
        canvas.create_line(left, top, left, top + (self.lines-1) * distance)
        canvas.create_line(right, top, right, top + (self.lines-1) * distance)
        # draws clef:
        if self.clef == 3:
            clef = listOfClefs[0]
        else:
            clef = listOfClefs[self.clef]
        (clefX, clefY) = positionClef(self.clef, left, top)
        canvas.create_image(clefX, clefY, image=clef)
        # draws time signature:
        clefDistance = 37
        canvas.create_text(left+clefDistance, top, text=str(self.timeTop), 
                           anchor=NW, font='Times 20 bold')
        canvas.create_text(left+clefDistance, top+2*distance, 
                           text=str(self.timeBot), anchor=NW, 
                           font='Times 20 bold')
        # draws measures:
        actualHeight = height - 10
        startDistance = 30 + 10
        startLine = left + startDistance
        width = right - left - startDistance
        measureWidth = width/self.measureCount
        for i in xrange(self.measureCount):
            startMeasure = startLine + measureWidth * i
            self.measures[i].draw(canvas, startMeasure, measureWidth, top, 
                                  height-10, distance)

class Page(object):
    def __init__(self, clef, timeTop, timeBot):
        self.clef = clef
        self.staffCount = 6
        self.staffHeight = 50
        self.staves = []
        for i in xrange(self.staffCount):
            self.staves += [Staff(self.clef, timeTop, timeBot, i + 1)]
        self.pageMargin = 100

    def draw(self, canvas, left, top, right, bot):
        spacing = 2
        (staffL, staffR) = (left+self.pageMargin, right-self.pageMargin)
        for i in xrange(self.staffCount):
            staffTop = top + spacing * self.staffHeight * (i + 1)
            self.staves[i].draw(canvas,self.staffHeight,staffL,staffR,staffTop)

################################################################################
# init functions
################################################################################

def initFn(data):
    data.windowTitle = "composYour"
    data.audioDictionary = generateAudioDictionary()
    data.textSize = 20
    # init helper functions:
    data.topSize = data.height/8
    data.sideWidth = data.height/4
    data.sideHeight = data.topSize/2
    welcomeInit(data)
    initTopBar(data)
    initSidebar(data)
    initSave(data)
    # trackers:
    data.page = 0                   # keeps track of current page
    data.mode = ''
    data.selectedAdd = ''
    data.wrongMeasures = []
    data.beatChecked = False
    # should initialize the framework and keep track of what is selected
    # also should keep track of what mode we are in (add, remove, select)

def welcomeInit(data):
    data.screen = 0
    data.margin = 20
    data.clef = 3
    data.timeTop = 0
    data.timeBot = 0
    data.topOptions = 12
    data.options = [2, 4, 8]
    data.entry = Entry(width=30)

def initTopBar(data):
    data.center = data.topSize/2
    data.saveX = data.sideWidth
    data.addX = data.saveX + data.topSize
    data.selectX = data.addX + data.topSize
    data.removeX = data.selectX + data.topSize
    data.playX = data.removeX + data.topSize
    data.helpX = data.width - data.topSize
    data.checkX = data.helpX - data.topSize
# initializes coordinates of top bar buttons

def initSidebar(data):
    # centering:
    (data.centerX, data.centerY) = (data.sideWidth/2, data.sideHeight/2)
    # horizontal divisions:
    data.noteY = data.topSize + data.sideHeight
    data.restY = data.noteY + data.sideHeight
    data.pageNumberY = data.height - data.sideHeight
    # vertical divisions:
    data.newX = data.sideWidth/2
    data.pageLeftX = data.sideWidth * .25
    data.pageCenterX = data.pageLeftX/2
    data.pageRightX = data.sideWidth * .75
# initializes coordinates of side bar buttons

def initSave(data):
    data.fileName = Entry(width=30)
    (data.saveBoxW, data.saveBoxH) = (300, 150)
    (data.saveButtonW, data.saveButtonH) = (60, 30)

################################################################################
# draw functions
################################################################################

def drawFn(canvas, data):
    if data.screen == 4:
        drawPrettyBackgrounds(canvas, data)
        drawTopBar(canvas, data)
        drawSidebar(canvas, data)
        drawWrongMeasures(canvas, data)
        drawPage(canvas, data)
        drawSelectedMode(canvas, data)
        if data.mode == 'Add':
            drawSelectedAdd(canvas, data)
        elif data.mode == 'Help':
            drawHelp(canvas, data)
        elif data.mode == 'Save':
            drawSave(canvas, data)
    else:
        drawWelcome(canvas, data)

def drawWelcome(canvas, data):
    (w, h, m) = (data.width, data.height, data.margin)
    (centerW, thirdH) = (w/2, h/3)
    canvas.create_rectangle(0, 0, w, h, fill='Lemon Chiffon', width=0)
    if data.screen == 0:
        canvas.create_text(centerW,thirdH-thirdH/2,text='Welcome to composYour',
                           font='Times 80 bold', fill='VioletRed1')
        text = 'the music composition software\nwhere you can compose music and\
\ncompose yourself at the same time'
        canvas.create_text(centerW,(thirdH*3)/2,text=text,font='Times 50 bold', 
                           fill='PaleVioletRed1', justify=CENTER)
        canvas.create_text(w/2,(thirdH*5)/2,text='Click anywhere to begin >>>',
                           fill='MediumPurple2', font='Times 80 bold')
    elif data.screen == 1:
        text = 'If you would like to open\na previous project...'
        canvas.create_text(centerW, thirdH/2, text=text, font='Times 80 bold', 
                           fill='SeaGreen2', justify=CENTER)
        canvas.create_text(centerW,thirdH*1.25,text='Input the file name here:',
                           fill='SteelBlue1', font='Times 30 bold')
        data.entry.place(x=w/2, y=h/2, anchor=CENTER)
        # buttons:
        canvas.create_rectangle(m, 2*thirdH+m, centerW-m, h-m, 
                                outline='PaleVioletRed1', width=3)
        canvas.create_text(centerW/2, h-thirdH/2, text='Open\nProject', 
                           fill='PaleVioletRed1', font='Times 80 bold', 
                           justify=CENTER)
        canvas.create_rectangle(centerW+m, 2*thirdH+m, w-m, h-m, 
                                outline='MediumPurple2', width=3)
        canvas.create_text(w-centerW/2, h-thirdH/2, text='New\nProject', 
                           fill='MediumPurple2', font='Times 80 bold', 
                           justify=CENTER)
    elif data.screen == 2:
        # choose text:
        textLower = h/3
        canvas.create_text(centerW, textLower/2, text='Choose a Clef', 
                           fill='SeaGreen2', font='Times 80 bold')
        # clefs:
        drawClefsMenu(canvas, data, textLower, thirdH)
        # submit button:
        (lowerX, upperX) = (w/3, w/3 *2)
        (lowerY, upperY) = (thirdH * 2 + 2*m, h-2*m)
        canvas.create_rectangle(lowerX+m, lowerY+m, upperX-m, upperY-m, 
                                outline='salmon1', width=3)
        canvas.create_text(w/2, thirdH * 2 + thirdH/2, text='Submit', 
                           fill='salmon1', font='Times 80 bold')
    elif data.screen == 3:
        textLower = h/7
        # choose text:
        canvas.create_text(centerW, textLower/2, text='Choose a Time Signature',
                           fill='MediumPurple3', font='Times 60 bold')
        drawTimeMenu(canvas, data, textLower, h/7)
        # submit button:
        (lowerX, upperX) = (w/3, w/3 *2)
        (lowerY, upperY) = (thirdH * 2 + 2*m, h-2*m)
        canvas.create_rectangle(lowerX+m, lowerY+m, upperX-m, upperY-m, 
                                outline='PaleVioletRed1', width=3)
        canvas.create_text(w/2, thirdH * 2 + thirdH/2, text='Compose!', 
                           fill='PaleVioletRed1', font='Times 60 bold')

def drawTimeMenu(canvas, data, startY, height):
    (w, h, m, centerW) = (data.width, data.height, data.margin, data.width/2)
    # selectCircle:
    r = 40
    if data.timeTop != 0:
        x = w/(data.topOptions+1) * (data.timeTop)
        y = startY * 2 + height/2
        canvas.create_oval(x-r, y-r, x+r, y+r, outline='MediumPurple2', width=4)
    if data.timeBot != 0:
        x = w/(len(data.options)+1) * (data.options.index(data.timeBot) + 1)
        y = startY * 4 + height/2
        canvas.create_oval(x-r, y-r, x+r, y+r, outline='MediumPurple2', width=4)
    # top:
    canvas.create_text(centerW, startY+height/2, text='Number of Beats', 
                       fill='SteelBlue2', font='Times 40 bold')
    for i in xrange(data.topOptions):
        x = w/(data.topOptions+1) * (i + 1)
        y = startY * 2 + height/2
        canvas.create_text(x, y, text=str(i+1), fill='SteelBlue1', 
                           font='Times 40 bold')
    # bot:
    canvas.create_text(centerW, startY*3+height/2, text='Note Value', 
                       fill='SeaGreen3', font='Times 40 bold')
    for i in xrange(len(data.options)):
        x = w/(len(data.options)+1) * (i + 1)
        y = startY * 4 + height/2
        canvas.create_text(x, y, text=str(data.options[i]),font='Times 40 bold',
                           fill='SeaGreen2')

def drawClefsMenu(canvas, data, startY, height):
    (w, h, m, highlight) = (data.width, data.height, data.margin, 5)
    loadClefImagesBecauseTkinterIsStupid()
    (thirdX, thirdY) = (w/3, h/3)
    centerY = startY + height/2
    endY = startY + height
    colors = ['PaleVioletRed1', 'SteelBlue1', 'MediumPurple2']
    for i in xrange(len(TkinterSucks)):
        clef = TkinterSucks[i]
        x = i * thirdX + thirdX/2
        canvas.create_image(x, centerY, image=clef)
        canvas.create_rectangle(i*thirdX+m, startY, (i+1)*thirdX-m, endY, width=3, outline=colors[i])
    # clef labels:
    canvas.create_text(thirdX/2, thirdY+m, text='Treble Clef', 
                       font='Times 40 bold', fill=colors[0], anchor=N)
    canvas.create_text(thirdX*3/2, thirdY+m, text='Alto Clef', 
                       font='Times 40 bold', fill=colors[1], anchor=N)
    canvas.create_text(thirdX*5/2, thirdY+m, text='Bass Clef', 
                       font='Times 40 bold', fill=colors[2], anchor=N)
    # clef description:
    trebleText = 'Most common clef used today'
    canvas.create_text(thirdX/2, thirdY*2-m*2, text=trebleText, 
                       font='Times 22 bold', fill=colors[0], anchor=S)
    altoText = 'Not so common. Used for violas! ;)'
    canvas.create_text(thirdX*3/2, thirdY*2-m*2, text=altoText, 
                       font='Times 22 bold', fill=colors[1], anchor=S)
    bassText = 'Used for lower ranges'
    canvas.create_text(thirdX*5/2, thirdY*2-m*2, text=bassText, 
                       font='Times 22 bold', fill=colors[2], anchor=S)
    canvas.create_rectangle(data.clef*thirdX+m+highlight, startY+highlight,
                            (data.clef+1)*thirdX-m-highlight, endY-highlight,
                            width=3, outline='SeaGreen2')

def drawPrettyBackgrounds(canvas, data):
    (w, h, m) = (data.width, data.height, data.margin)
    (top, sideW, sideH) = (data.topSize, data.sideWidth, data.sideHeight)
    canvas.create_rectangle(0, 0, sideW, h, fill='Lemon Chiffon')
    canvas.create_rectangle(0, h-sideH, sideW, h, fill='SeaGreen2')
    canvas.create_rectangle(0, 0, w, top, fill='SkyBlue2')
    canvas.create_rectangle(0, 0, sideW, top, fill='MediumPurple2')
    canvas.create_rectangle(w-2*top, 0, w, top, fill='PaleVioletRed1')

def drawTopBar(canvas, data):
    canvas.create_line(0, data.topSize, data.width, data.topSize, width=2)
    # add button:
    canvas.create_line(data.addX, 0, data.addX, data.topSize)
    canvas.create_text(data.addX - data.center, data.center, text='Add', 
                       font='Times '+str(data.textSize)+' bold')
    # select button:
    canvas.create_line(data.selectX, 0, data.selectX, data.topSize)
    canvas.create_text(data.selectX-data.center,data.center,text='Select', 
                       font='Times '+str(data.textSize)+' bold')
    # remove button:
    canvas.create_line(data.removeX, 0, data.removeX, data.topSize)
    canvas.create_text(data.removeX-data.center,data.center,text='Remove', 
                       font='Times '+str(data.textSize)+' bold')
    # play button:
    canvas.create_line(data.playX, 0, data.playX, data.topSize)
    canvas.create_text(data.playX-data.center, data.center, text='Play',  
                       font='Times '+str(data.textSize)+' bold')
    # beat check button:
    canvas.create_line(data.checkX, 0, data.checkX, data.topSize)
    canvas.create_text(data.checkX+data.center,data.center, text=' Beat\nCheck', 
                       font='Times '+str(data.textSize)+' bold')
    # help button:
    canvas.create_line(data.helpX, 0, data.helpX, data.topSize)
    canvas.create_text(data.helpX+data.center, data.center, text='Help',  
                       font='Times '+str(data.textSize)+' bold')

def drawSidebar(canvas, data):
    canvas.create_line(data.sideWidth, 0, data.sideWidth, data.height, width=2)
    # new button:
    canvas.create_line(data.newX, 0, data.newX, data.topSize)
    canvas.create_text(data.sideWidth/4, data.topSize/2, text='New',  
                       font='Times '+str(data.textSize)+' bold')
    # save button:
    canvas.create_line(data.saveX, 0, data.saveX, data.topSize)
    canvas.create_text((data.sideWidth/4)*3, data.topSize/2, text='Save',  
                       font='Times '+str(data.textSize)+' bold')
    # note button:
    canvas.create_line(0, data.noteY, data.sideWidth, data.noteY)
    canvas.create_text(data.centerX, data.noteY-data.centerY, text='Note',  
                       font='Times '+str(data.textSize)+' bold')
    # rest button:
    canvas.create_line(0, data.restY, data.sideWidth, data.restY)
    canvas.create_text(data.centerX, data.restY-data.centerY, text='Rest',  
                       font='Times '+str(data.textSize)+' bold')
    # page flip:
    canvas.create_line(0, data.pageNumberY, data.sideWidth, data.pageNumberY)
    canvas.create_text(data.centerX, data.pageNumberY+data.centerY,  
                       text='Page '+str(data.page+1)+'/'+str(len(data.score)),  
                       font='Times '+str(data.textSize)+' bold')
    canvas.create_line(data.pageLeftX, data.pageNumberY, data.pageLeftX, data.height)
    canvas.create_line(data.pageRightX, data.pageNumberY, data.pageRightX, data.height)
    canvas.create_text(data.pageCenterX, data.pageNumberY+data.centerY,  
                       text='<', font='Times '+str(data.textSize)+' bold')
    canvas.create_text(data.sideWidth-data.pageCenterX, data.pageNumberY+data.centerY,  
                       text='>', font='Times '+str(data.textSize)+' bold')

def drawWrongMeasures(canvas, data):
    margin = 5
    if data.beatChecked == True and len(data.wrongMeasures) > 0:
        sorryString = 'Oh no! :('
        errors = [sorryString] + data.wrongMeasures
        for i in xrange(len(errors)):
            spacing = 20
            y = data.restY + margin * 2 + i * spacing
            canvas.create_text(margin, y, text=errors[i], anchor=NW, font='Times 14')
    elif data.beatChecked == True and len(data.wrongMeasures) == 0:
        (x, y) = (margin, data.restY + 2 * margin)
        text = 'All good!'+('\n'*32)+'...for now... >:)'
        canvas.create_text(margin, y, text=text, anchor=NW, font='Times 14')

def drawSelectedMode(canvas, data):
    margin = 5
    if data.mode == 'Save':
        canvas.create_rectangle(data.sideWidth/2+margin, margin, data.saveX-margin,  
                                data.topSize-margin, outline='DeepPink2', width=3)
    elif data.mode == 'Add':
        canvas.create_rectangle(data.saveX+margin, margin, data.addX-margin, 
                                data.topSize-margin, outline='DeepPink2', width=3)
    elif data.mode == 'Select':
        canvas.create_rectangle(data.addX+margin, margin, data.selectX-margin, 
                                data.topSize-margin, outline='DeepPink2', width=3)
    elif data.mode == 'Remove':
        canvas.create_rectangle(data.selectX+margin, margin, data.removeX-margin, 
                                data.topSize-margin, outline='DeepPink2', width=3)
    elif data.mode == 'Help':
        canvas.create_rectangle(data.helpX+margin, margin, data.width-margin, 
                                data.topSize-margin, outline='DeepPink2', width=3)
    elif data.mode == 'Play':
        canvas.create_rectangle(data.removeX+margin, margin, data.playX-margin,
                                data.topSize-margin, outline='DeepPink2', width=3)

def drawSelectedAdd(canvas, data):
    margin = 5
    th = data.sideWidth/3
    if data.selectedAdd == 'Note':
        canvas.create_rectangle(margin, data.topSize+margin, data.sideWidth-margin, 
                                data.noteY-margin, outline='MediumPurple1', width=3)
    elif data.selectedAdd == 'Rest':
        canvas.create_rectangle(margin, data.noteY+margin, data.sideWidth-margin, 
                                data.restY-margin, outline='MediumPurple1', width=3)

def drawPage(canvas, data):
    (left, top) = (data.sideWidth, data.topSize)
    # draws current page:
    data.score[data.page].draw(canvas, left, top, data.width, data.height)

def drawHelp(canvas, data):
    canvas.create_rectangle(data.sideWidth, data.topSize, data.width, data.height, 
                            fill='white')
    margin = 10
    centerX = data.sideWidth + (data.width-data.sideWidth)/2
    centerY = data.topSize + (data.height-data.topSize)/2
    helpText = '''Hi! Welcome to composYour ^^

To add notes to the music staff, press Add and click where you would like to add the note
To select a note, press Select and choose the note you would like to select
To play what is on your current page, press Play

While in Add mode, you can:
- Add notes by selecting Note in the sidebar
- Add rests by selecting Rest in the sidebar

While in Select mode, you can:
- Change the pitch of a note by selecting it and pressing the Up or Down arrow key
- Change the duration of a note or rest by selecting it and pressing the Left or Right arrow key
- Make a note sharp or flat by selecting it and pressing 's' for sharp and 'f' for flat
- Remove sharps or flats from a note by selecting it and pressing 'n' for natural

While in Remove mode, you can:
- Remove multiple notes by selecting them and clicking Remove

To check that your current page correctly follows the time signature so far, click Beat Check
The results of your Beat Check test will appear on the left sidebar

To change the page or add pages, click on the arrows at the bottom left of the screen

To save your work so far, click the Save button on the top left and enter in a file name
To start over or open a different piece, press New

Click Add or Select to get started!'''
    canvas.create_text(centerX, centerY, text=helpText, fill='purple3', font='Times 20 bold', justify=CENTER)

def drawSave(canvas, data):
    (centerX, centerY) = (data.width/2, data.height/2)
    (boxW, boxH) = (data.saveBoxW, data.saveBoxH)
    canvas.create_rectangle(centerX-boxW/2, centerY-boxH/2, centerX+boxW/2, 
                            centerY+boxH/2, fill='Lemon Chiffon')
    canvas.create_text(centerX, centerY-boxH/3, text='Name your composition:', 
                       font='Times 20 bold')
    data.fileName.place(x=centerX, y=centerY, anchor=CENTER)
    (buttonW, buttonH) = (data.saveButtonW, data.saveButtonH)
    canvas.create_rectangle(centerX-buttonW/2, centerY+boxH/3-buttonH/2,
                            centerX+buttonW/2, centerY+boxH/3+buttonH/2, fill='PaleVioletRed1')
    canvas.create_text(centerX, centerY+boxH/3, text='Save', font='Times 20 bold')

################################################################################
# event functions
################################################################################

def mouseFn(event, data):
    if data.screen == 4:
        if data.mode == 'Save':
            fileSave(event, data)
            if data.mode != 'Remove':
                deremoveAll(data)
                deselectAll(data)
        else:
            if data.mode == 'Remove':
                deselectAll(data)
                removeWithoutSelect(event, data)
                remove(event, data)
            if data.mode == 'Select':
                select(event, data)
                remove(event, data)
                if data.mode != 'Remove':
                    deremoveAll(data)
            elif data.mode == 'Add':
                deselectAll(data)
                chooseAdd(event, data)
                if data.selectedAdd != '':
                    add(event, data)
                if data.mode != 'Remove':
                    deremoveAll(data)
            changingModes(event, data)
            changingPage(event, data)
            beatCheck(event, data)
            clickPlay(event, data)
    else:
        welcomeMouse(event, data)

def welcomeMouse(event, data):
    (w, h, m) = (data.width, data.height, data.margin)
    if data.screen == 0:
        if 0 < event.x < w and 0 < event.y < h:
            data.screen += 1
    elif data.screen == 1:
        if 2*(h/3) < event.y < h: 
            if w/2 < event.x < w:
                data.page = 0
                data.entry.place_forget()
                data.screen += 1
            elif 0 < event.x < w/2:
                try:
                    data.entry.place_forget()
                    oldProject = data.entry.get()
                    loadData(data, oldProject)
                    data.page = 0
                    data.score = [Page(data.clef, data.timeTop, data.timeBot)]
                    loadNotes(data, oldProject)
                    data.screen = 4
                except: pass
    elif data.screen == 2:
        if (h/3) < event.y < (h/3) * 2:
            data.clef = event.x / (w/3)
        elif (h/3)*2 < event.y < h and w/4 < event.x < (w/4)*3:
            if data.clef == 0 or data.clef == 1 or data.clef == 2:
                data.screen += 1
    elif data.screen == 3:
        if (h/7) * 2 < event.y < (h/7) * 3:
            data.timeTop = event.x / (w/data.topOptions) + 1
        elif (h/7) * 4 < event.y < (h/7) * 5:
            data.timeBot = data.options[event.x / (w/len(data.options))]
        elif (h/3)*2 < event.y < h and w/4 < event.x < (w/4)*3:
            if data.timeTop != 0 and data.timeBot != 0:
                data.score = [Page(data.clef, data.timeTop, data.timeBot)]
                data.screen += 1

def changingModes(event, data):
    (addLeft, addRight) = (data.addX-data.topSize, data.addX)
    (selectLeft, selectRight) = (data.selectX-data.topSize, data.selectX)
    (removeLeft, removeRight) = (data.removeX-data.topSize, data.removeX)
    (helpLeft, helpRight) = (data.helpX, data.width)
    if data.sideWidth/2 < event.x < data.sideWidth and 0<event.y<data.topSize:
        data.mode = 'Save'
    elif addLeft <= event.x <= addRight and 0 <= event.y <= data.topSize:
        data.mode = 'Add'
    elif selectLeft <= event.x <= selectRight and 0 <= event.y <= data.topSize:
        data.mode = 'Select'
    elif removeLeft <= event.x <= removeRight and 0 <= event.y <= data.topSize:
        data.mode = 'Remove'
    elif helpLeft <= event.x <= helpRight and 0 <= event.y <= data.topSize:
        data.mode = 'Help'
    elif 0 < event.x < data.sideWidth/2 and 0 < event.y < data.topSize:
        data.screen = 1

def changingPage(event, data):
    if data.pageNumberY < event.y < data.height:
        if 0 < event.x < data.pageLeftX:
            (data.wrongMeasures, data.beatChecked) = ([], False)
            if data.page > 0:
                data.page -= 1
        elif data.pageRightX < event.x < data.sideWidth:
            (data.wrongMeasures, data.beatChecked) = ([], False)
            if data.page + 1 == len(data.score):
                data.score += [Page(data.clef, data.timeTop, data.timeBot)]
                data.page += 1
            elif data.page < len(data.score):
                data.page += 1

def clickPlay(event, data):
    if data.removeX < event.x < data.playX and 0 < event.y < data.topSize:
        data.mode = 'Play'
        for staff in data.score[data.page].staves:
            for measure in staff.measures:
                for item in measure.notes:
                    audio = data.audioDictionary[item.fileName]
                    segment = .6 * 1000 * item.duration
                    offset = 1000
                    audioSegment = audio[offset:offset+segment]
                    play(audioSegment)
        data.mode = ''

def beatCheck(event, data):
    if data.checkX < event.x < data.helpX and 0 < event.y < data.topSize:
        data.beatChecked = True
        data.wrongMeasures = []
        for staff in data.score[data.page].staves:
            for measure in staff.measures:
                data.wrongMeasures+=measure.beatCheck(data.timeTop,data.timeBot)

def select(event, data):
    if not (data.addX < event.x < data.removeX and 0 < event.y < data.topSize):
        for staff in data.score[data.page].staves:
            for measure in staff.measures:
                for item in measure.notes:
                    item.selectTest(event)

def remove(event, data):
    if data.selectX < event.x < data.removeX and 0 < event.y < data.topSize:
        for staff in data.score[data.page].staves:
            for measure in staff.measures:
                if data.mode == 'Remove':
                    itemsToRemove = []
                    for item in measure.notes:
                        if item.removed == True:
                            itemsToRemove.append(item)
                    for item in itemsToRemove:
                        measure.remove(item)

def removeWithoutSelect(event, data):
    if not (data.addX < event.x < data.removeX and 0 < event.y < data.topSize):
        for staff in data.score[data.page].staves:
            for measure in staff.measures:
                for item in measure.notes:
                    item.removeTest(event)

def chooseAdd(event, data):
    (left, right) = (0, data.sideWidth)
    th = data.sideWidth/3
    if left < event.x < right and data.topSize < event.y < data.noteY:
        data.selectedAdd = 'Note'
    elif left < event.x < right and data.noteY < event.y < data.restY:
        data.selectedAdd = 'Rest'

def add(event, data):
    for staff in data.score[data.page].staves:
        for measure in staff.measures:
            if data.selectedAdd == 'Note':
                measure.addNote(event)
            elif data.selectedAdd == 'Rest':
                measure.addRest(event)

def fileSave(event, data):
    (centerX, centerY) = (data.width/2, data.height/2)
    (boxW, boxH) = (data.saveBoxW, data.saveBoxH)
    (lowerX, upperX) = (centerX-boxW/2, centerX+ boxW/2)
    (lowerY, upperY) = (centerY-boxH/2, centerY+ boxH/2)
    (buttonW, buttonH) = (data.saveButtonW, data.saveButtonH)
    if lowerX < event.x < upperX and lowerY < event.y < upperY:
        if centerX-buttonW/2 < event.x < centerX+buttonW/2:
            if centerY+boxH/3-buttonH/2< event.y < centerY+boxH/3+buttonH/2:
                if data.fileName.get() != '':
                    data.fileName.place_forget()
                    data.mode = ''
                    writeFile(data)
    else:
        data.fileName.place_forget()
        data.mode = ''

def keyFn(event, data):
    if data.screen == 4:
        if event.keysym == 'Up':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True and type(item) == Note:
                            item.changePitch(1)
        elif event.keysym == 'Down':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True and type(item) == Note:
                            item.changePitch(-1)
        elif event.keysym == 'Left':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True:
                            item.changeRhythm(-1)
        elif event.keysym == 'Right':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True:
                            item.changeRhythm(1)
        elif event.keysym == 'f':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True and type(item) == Note:
                            item.changeAccidental('f')
        elif event.keysym == 's':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True and type(item) == Note:
                            item.changeAccidental('s')
        elif event.keysym == 'n':
            for staff in data.score[data.page].staves:
                for measure in staff.measures:
                    for item in measure.notes:
                        if item.selected == True and type(item) == Note:
                            item.changeAccidental('')

################################################################################
# highest level function
################################################################################

def compose():
    eventBasedAnimation.run(initFn=initFn, drawFn=drawFn, mouseFn=mouseFn, 
                            keyFn=keyFn, width=1200, height=800)

compose()