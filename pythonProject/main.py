import speech_recognition as sr
import os
from pydub import AudioSegment
from pydub.playback import play
from pydub.silence import split_on_silence
from design import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog


from Dialogtext import Ui_DialogText
from Dialogdetails import  Ui_DialogDetails


class DialogDetails(QtWidgets.QDialog, Ui_DialogDetails):

    def __init__(self, old, new, parent=None):
        super(DialogDetails, self).__init__(parent)
        self.setupUi(self)

        self.lengthorg.setText(str(old) + "s")
        self.lengthresult.setText(str(new) + "s")
        self.procents.setText(str(int((old - new)*100/old)) + "%")



class DialogText(QtWidgets.QDialog, Ui_DialogText):
    def __init__(self, text, parent=None):
        super(DialogText, self).__init__(parent)
        self.setupUi(self)
        self.plainTextEdit.setPlainText(text)



class Main_Window(QtWidgets.QMainWindow, Ui_MainWindow):
    oldlength = 0
    newlength = 0
    procentsstr = ""
    original_file_path=""
    clear1_file=""
    clear2_file=""
    whole_text = ""
    def __init__(self,  *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        self.Delete.clicked.connect(self.cut)
        self.actionSave_2.triggered.connect(self.save)
        self.actionSave_Text.triggered.connect(self.save_text)
        self.Playold.clicked.connect(self.playorg)
        self.Playnew.clicked.connect(self.playnew)

        self.Delete.clicked.connect(self.progress_bar)
        self.step = 0
        self.progressBar.setValue(self.step)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_func)

        self.FullText.clicked.connect(self.openTextDialog)
        self.Details.clicked.connect(self.openDetailDialog)

        self.pushButton.clicked.connect(self.load)
        self.LoadFile.clicked.connect(self.loadfileclick)
        self.Microphone.clicked.connect(self.microphoneclick)


    def clear_out(self, clear_stage):
        r = sr.Recognizer()
        flag=False
        if clear_stage == 1:
            sound = AudioSegment.from_wav(self.original_file_path)
        else:
            sound = self.clear1_file

        if clear_stage==1:
            self.whole_text = ""
            chunks = split_on_silence(sound,
                min_silence_len = 500,
                silence_thresh = sound.dBFS-14,
                keep_silence=500,
            )
        else:
            chunks = split_on_silence(sound,
              min_silence_len=250,
              silence_thresh=sound.dBFS - 14,
              keep_silence=250, )
        folder_name = "audio-chunks"
        if not os.path.isdir(folder_name):
            os.mkdir(folder_name)
        for i, audio_chunk in enumerate(chunks, start=1):

            chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
            audio_chunk.export(chunk_filename, format="wav")


            audio_chunk.export(chunk_filename, format="wav")
            with sr.AudioFile(chunk_filename) as source:
                audio_listened = r.record(source)
                try:
                    text = r.recognize_google(audio_listened)
                except sr.UnknownValueError as e:
                    text = ""

                else:
                    text = f"{text.capitalize()}. "
                    if clear_stage==1:
                         self.whole_text += text
                         self.whole_text += " "

                    sound_chunk=AudioSegment.from_wav(chunk_filename)
                    if flag==False:
                        File_out=sound_chunk
                        flag=True
                    else:
                        File_out+=sound_chunk

        if clear_stage == 1:
            self.clear1_file = File_out
        else :
            self.clear2_file = File_out


    def progress_bar(self):
        self.timer.start(50)

    def update_func(self):
        self.step += 1
        self.progressBar.setValue(self.step)
        if self.step == 100:
            self.timer.stop()
            self.Playnew.setEnabled(True)
            self.FullText.setEnabled(True)
            self.Details.setEnabled(True)


    def loadfileclick(self):
        self.pushButton.setEnabled(True)
        self.pushButton.setText("Load from file")

    def microphoneclick(self):
        self.pushButton.setEnabled(True)
        self.pushButton.setText("Record")


    def load(self):
        self.step = 0
        self.Playold.setEnabled(True)
        self.Delete.setEnabled(True)
        self.Playnew.setEnabled(False)
        self.FullText.setEnabled(False)
        self.Details.setEnabled(False)

        if self.LoadFile.isChecked():
            self.loadfile()
        elif self.Microphone.isChecked():
            self.record()

    def loadfile(self):
        p = QFileDialog.getOpenFileName(self, "OpenFile")
        self.original_file_path = p[0]

    def record(self):
        r = sr.Recognizer()
        mic=sr.Microphone()
        with mic as audio_file:
            r.adjust_for_ambient_noise(audio_file)
            audio=r.listen(audio_file)
        with open("MIC.wav", "wb") as f:
            f.write(audio.get_wav_data())
        self.original_file_path="MIC.wav"


    def cut(self):
        self.clear_out(1)
        self.clear_out(2)
        self.file_info()


    def file_info(self):

        sound = AudioSegment.from_wav(self.original_file_path)

        total_in_ms1 = len(sound) / 1000
        self.oldlength = total_in_ms1

        total_in_ms2 = len(self.clear2_file) / 1000
        self.newlength = total_in_ms2


    def save(self):
        o = QFileDialog.getSaveFileName(self)
        out = o[0]
        self.clear2_file.export(out + ".wav", format="wav")

    def save_text(self):
        o = QFileDialog.getSaveFileName(self)
        out = o[0]
        file = open(out + ".txt", "w")
        file.write(self.whole_text)
        file.close()

    def playorg(self):
        song = AudioSegment.from_wav(self.original_file_path)
        play(song)

    def playnew(self):
        play(self.clear2_file)


    def setprocent(self):
        self.procentsstr = str(int((self.oldlength - self.newlength)*100/self.oldlength)) + "%"
        self.procents.setText(self.procentsstr)


    def openTextDialog(self):

        w = DialogText(self.whole_text)
        w.setWindowTitle("Transcribed text")
        w.exec_()

    def openDetailDialog(self):
        w = DialogDetails(self.oldlength, self.newlength)
        w.setWindowTitle("Info")
        w.exec()


if __name__ == "__main__":

    app=QtWidgets.QApplication([])
    window=Main_Window()
    window.setWindowTitle('Speech Cleaning Software')
    window.show()

    app.exec_()